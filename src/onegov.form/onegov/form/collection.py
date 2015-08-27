import warnings

from datetime import datetime, timedelta
from onegov.core.utils import normalize_for_url
from onegov.form.errors import UnableToComplete
from onegov.form.fields import UploadField
from onegov.form.models import (
    FormDefinition,
    FormSubmission,
    FormSubmissionFile
)
from sedate import replace_timezone, utcnow
from sqlalchemy import inspect, func, not_, exc
from uuid import uuid4


class FormCollection(object):
    """ Manages a collection of forms and form-submissions. """

    def __init__(self, session):
        self.session = session

    @property
    def definitions(self):
        return FormDefinitionCollection(self.session)

    @property
    def submissions(self):
        return FormSubmissionCollection(self.session)

    def scoped_submissions(self, name, ensure_existance=True):
        if not ensure_existance or self.definitions.by_name(name):
            return FormSubmissionCollection(self.session, name)

    def get_definitions_with_submission_count(self):
        """ Returns all form definitions and the number of submissions
        belonging to those definitions, in a single query.

        The number of submissions is stored on the form definition under the
        ``submissions_count`` attribute.

        Only submissions which are 'complete' are considered.

        """
        submissions = self.session.query(
            FormSubmission.name,
            func.count(FormSubmission.id).label('count')
        )
        submissions = submissions.filter(FormSubmission.state == 'complete')
        submissions = submissions.group_by(FormSubmission.name).subquery()

        definitions = self.session.query(FormDefinition, submissions.c.count)
        definitions = definitions.outerjoin(
            submissions, submissions.c.name == FormDefinition.name
        )
        definitions = definitions.order_by(FormDefinition.name)

        for form, submissions_count in definitions.all():
            form.submissions_count = submissions_count or 0
            yield form


class FormDefinitionCollection(object):
    """ Manages a collection of forms. """

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FormDefinition)

    def add(self, title, definition,
            type=None, meta=None, content=None, name=None):
        """ Add the given form to the database. """

        # look up the right class depending on the type
        _mapper = inspect(FormDefinition).polymorphic_map.get(type)
        form = (_mapper and _mapper.class_ or FormDefinition)()

        form.name = name or normalize_for_url(title)
        form.title = title
        form.definition = definition
        form.type = type
        form.meta = meta or {}
        form.content = content or {}

        # try to parse the form (which will throw errors if there are problems)
        assert form.form_class

        self.session.add(form)
        self.session.flush()

        return form

    def delete(self, name, with_submissions=False):
        """ Delete the given form. Only possible if there are no submissions
        associated with it, or if ``with_submissions`` is True.

        Note that pending submissions are removed automatically, only complete
        submissions have a bearing on ``with_submissions``.

        """
        submissions = self.session.query(FormSubmission)
        submissions = submissions.filter(FormSubmission.name == name)

        if not with_submissions:
            submissions = submissions.filter(FormSubmission.state == 'pending')

        submissions.delete()

        # this will fail if there are any submissions left
        self.query().filter(FormDefinition.name == name).delete('fetch')
        self.session.flush()

    def by_name(self, name):
        """ Returns the given form by name or None. """
        return self.query().filter(FormDefinition.name == name).first()


class FormSubmissionCollection(object):
    """ Manages a collection of submissions. """

    def __init__(self, session, name=None):
        self.session = session
        self.name = name

    def query(self):
        query = self.session.query(FormSubmission)

        if self.name is not None:
            query = query.filter(FormSubmission.name == self.name)

        return query

    def add(self, name, form, state, id=None):
        """ Takes a filled-out form instance and stores the submission
        in the database. The form instance is expected to have a ``_source``
        parameter, which contains the source used to build the form (as only
        forms with this source may be stored).

        This method expects the name of the form definition stored in the
        database. Use :meth:`add_external` to add a submissions whose
        definition is not stored in the form_definitions table.

        """

        assert hasattr(form, '_source')

        # this should happen way earlier, we just double check here
        if state == 'complete':
            assert form.validate()
        else:
            form.validate()

        # look up the right class depending on the type
        _mapper = inspect(FormSubmission).polymorphic_map.get(state)

        submission = (_mapper and _mapper.class_ or FormSubmission)()
        submission.id = id or uuid4()
        submission.name = name
        submission.state = state

        self.update(submission, form)

        self.session.add(submission)
        self.session.flush()

        # whenever we add a form submission, we remove all the old ones
        # which were never completed (this is way easier than having to use
        # some kind of cronjob ;)
        self.remove_old_pending_submissions(
            older_than=datetime.utcnow() - timedelta(days=1)
        )

        return submission

    def add_external(self, form, state, id=None):
        """ Takes a filled-out form instance and stores the submission
        in the database. The form instance is expected to have a ``_source``
        parameter, which contains the source used to build the form (as only
        forms with this source may be stored).

        In contrast to :meth:`add`, this method is meant for submissions whose
        definition is not stored in the form_definitions table.

        """

        return self.add(name=None, form=form, state=state, id=id)

    def complete_submission(self, submission):
        """ Changes the state to 'complete', if the data is valid. """

        assert submission.state == 'pending'

        if not submission.form_class(data=submission.data).validate():
            raise UnableToComplete()

        submission.state = 'complete'

        # by completing a submission we are changing it's polymorphic identity,
        # which is something SQLAlchemy rightly warns us about. Since we know
        # about it however (and deal with it using self.session.expunge below),
        # we should ignore this (and only this) warning.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                action="ignore",
                message=r'Flushing object',
                category=exc.SAWarning
            )
            self.session.flush()

        self.session.expunge(submission)

    def update(self, submission, form):
        """ Takes a submission and a form and updates the submission data
        as well as the files stored in a spearate table.

        """
        assert submission.id and submission.state

        submission.definition = form._source
        submission.data = form.data

        # never include the csrf token
        if form.meta.csrf and form.meta.csrf_field_name in submission.data:
            del submission.data[form.meta.csrf_field_name]

        # move uploaded files to a separate table
        files = set(
            field_id for field_id, field in form._fields.items()
            if isinstance(field, UploadField)
        )

        files_to_remove = set(
            id for id in files
            if submission.data.get(id) == {}
        )

        files_to_add = set(
            id for id in (files - files_to_remove)
            if submission.data.get(id)
            and not submission.data[id]['data'].startswith('@')
        )

        files_to_keep = files - files_to_remove - files_to_add

        # delete all files which are not part of the updated form
        # if no files are given, delete all files belonging to the submission
        query = self.session.query(FormSubmissionFile)
        query = query.filter(FormSubmissionFile.submission_id == submission.id)

        if files_to_keep:
            query = query.filter(not_(
                FormSubmissionFile.field_id.in_(files_to_keep)))

        query.delete('fetch')

        # store the new fields in the separate table
        for field_id in files_to_add:
            f = FormSubmissionFile(
                id=uuid4(),
                field_id=field_id,
                submission_id=submission.id,
                filedata=submission.data[field_id]['data'],
            )
            self.session.add(f)

            # replace the data in the submission with a reference
            submission.data[field_id]['data'] = '@{}'.format(f.id.hex)

            # we need to mark these changes as only top-level json changes
            # are automatically propagated
            submission.data.changed()

    def remove_old_pending_submissions(self, older_than,
                                       include_external=False):
        """ Removes all pending submissions older than the given date. The
        date is expected to be in UTC!

        """

        if older_than.tzinfo is None:
            older_than = replace_timezone(older_than, 'UTC')

        submissions = self.query()

        # delete the ones that were never modified
        submissions = submissions.filter(FormSubmission.state == 'pending')
        submissions = submissions.filter(
            FormSubmission.last_change < older_than)

        if not include_external:
            submissions = submissions.filter(FormSubmission.name != None)

        files = self.session.query(FormSubmissionFile)
        files = files.filter(FormSubmissionFile.submission_id.in_(
            submissions.with_entities(FormSubmission.id).subquery())
        )

        files.delete('fetch')
        submissions.delete('fetch')

    def by_state(self, state):
        return self.query().filter(FormSubmission.state == state)

    def by_name(self, name):
        """ Return all submissions for the given form-name. """
        return self.query().filter(FormSubmission.name == name).all()

    def by_id(self, id, state=None, current_only=False):
        """ Return the submission by id.

            :state:
                Only if the submission matches the given state.

            :current_only:
                Only if the submission is not older than one hour.
        """
        query = self.query().filter(FormSubmission.id == id)

        if state is not None:
            query = query.filter(FormSubmission.state == state)

        if current_only:
            an_hour_ago = utcnow() - timedelta(hours=1)
            query = query.filter(FormSubmission.last_change >= an_hour_ago)

        return query.first()

    def file_by_id(self, id):
        """ Returns the submission file with the given id or None. """
        query = self.session.query(FormSubmissionFile)
        query = query.filter(FormSubmissionFile.id == id)

        return query.first()

    def delete(self, submission):
        """ Deletes the given submission and all the files belonging to it. """
        self.session.delete(submission)
        self.session.flush()
