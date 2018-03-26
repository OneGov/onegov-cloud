import warnings

from datetime import datetime, timedelta
from onegov.core.crypto import random_token
from onegov.core.utils import normalize_for_url
from onegov.core.collection import GenericCollection
from onegov.file.utils import as_fileintent
from onegov.form.errors import UnableToComplete
from onegov.form.fields import UploadField
from onegov.form.models import (
    FormDefinition,
    FormSubmission,
    FormRegistrationWindow,
    FormFile
)
from sedate import replace_timezone, utcnow
from sqlalchemy import func, exc, inspect
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

    @property
    def registration_windows(self):
        return FormRegistrationWindowCollection(self.session)

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

    def add(self, title, definition, type=None, meta=None, content=None,
            name=None, payment_method='manual'):
        """ Add the given form to the database. """

        # look up the right class depending on the type
        form = FormDefinition.get_polymorphic_class(type, FormDefinition)()
        form.name = name or normalize_for_url(title)
        form.title = title
        form.definition = definition
        form.type = type
        form.meta = meta or {}
        form.content = content or {}
        form.payment_method = payment_method

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

    def add(self, name, form, state, id=None, payment_method=None,
            meta=None, email=None, spots=None):
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
            assert form.validate(), "the given form doesn't validate"
        else:
            form.validate()

        if name is None:
            definition = None
        else:
            definition = (
                self.session.query(FormDefinition)
                    .filter_by(name=name).one())

        if definition is None:
            registration_window = None
        else:
            registration_window = definition.current_registration_window

        if registration_window:
            assert registration_window.accepts_submissions(spots)

        # look up the right class depending on the type
        submission_class = FormSubmission.get_polymorphic_class(
            state, FormSubmission
        )

        submission = submission_class()
        submission.id = id or uuid4()
        submission.name = name
        submission.state = state
        submission.meta = meta or {}
        submission.email = email
        submission.registration_window = registration_window
        submission.spots = spots
        submission.payment_method = (
            payment_method or
            definition and definition.payment_method or
            'manual'
        )

        # extensions are inherited from definitions
        if definition:
            assert 'extensions' not in submission.meta, """
                For submissions based on definitions, the extensions need
                to be defined on the definition!
            """

            if 'extensions' in definition.meta:
                submission.meta['extensions'] = definition.meta['extensions']

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

    def add_external(self, form, state, id=None, payment_method=None,
                     meta=None, email=None):
        """ Takes a filled-out form instance and stores the submission
        in the database. The form instance is expected to have a ``_source``
        parameter, which contains the source used to build the form (as only
        forms with this source may be stored).

        In contrast to :meth:`add`, this method is meant for submissions whose
        definition is not stored in the form_definitions table.

        """

        return self.add(
            name=None,
            form=form,
            state=state,
            id=id,
            payment_method=payment_method,
            meta=meta,
            email=email,
        )

    def complete_submission(self, submission):
        """ Changes the state to 'complete', if the data is valid. """

        assert submission.state == 'pending'

        if not submission.form_obj.validate():
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

    def update(self, submission, form, exclude=None):
        """ Takes a submission and a form and updates the submission data
        as well as the files stored in a spearate table.

        """
        assert submission.id and submission.state

        # ignore certain fields
        exclude = exclude and set(exclude) or set()
        exclude.add(form.meta.csrf_field_name)  # never include the csrf token

        submission.definition = form._source
        submission.data = {
            k: v for k, v in form.data.items() if k not in exclude
        }

        # move uploaded files to a separate table
        files = set(
            field_id for field_id, field in form._fields.items()
            if isinstance(field, UploadField) and field_id not in exclude
        )

        files_to_remove = set(
            id for id in files
            if submission.data.get(id) == {}
        )

        files_to_add = set(
            id for id in (files - files_to_remove)
            if submission.data.get(id) and
            not submission.data[id]['data'].startswith('@')
        )

        files_to_keep = files - files_to_remove - files_to_add

        # delete all files which are not part of the updated form
        # if no files are given, delete all files belonging to the submission
        trash = [f for f in submission.files if f.note not in files_to_keep]

        for f in trash:
            self.session.delete(f)

        if trash and inspect(submission).persistent:
            self.session.refresh(submission)

        # store the new fields in the separate table

        for field_id in files_to_add:
            field = getattr(form, field_id)

            f = FormFile(
                id=random_token(),
                name=field.filename,
                note=field_id,
                reference=as_fileintent(
                    content=field.file,
                    filename=field.filename
                )
            )

            submission.files.append(f)

            # replace the data in the submission with a reference
            submission.data[field_id]['data'] = '@{}'.format(f.id)

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

        for submission in submissions:
            self.session.delete(submission)

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

    def delete(self, submission):
        """ Deletes the given submission and all the files belonging to it. """
        self.session.delete(submission)
        self.session.flush()


class FormRegistrationWindowCollection(GenericCollection):

    def __init__(self, session, name=None):
        super().__init__(session)
        self.name = name

    @property
    def model_class(self):
        return FormRegistrationWindow

    def query(self):
        query = super().query()

        if self.name:
            query = query.filter_by(FormRegistrationWindow.name == self.name)

        return query
