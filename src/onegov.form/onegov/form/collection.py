from delorean import Delorean
from datetime import datetime, timedelta
from onegov.core.utils import normalize_for_url
from onegov.form.fields import UploadField
from onegov.form.models import (
    FormDefinition,
    FormSubmission,
    FormSubmissionFile
)
from sqlalchemy import inspect, not_
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


class FormDefinitionCollection(object):
    """ Manages a collection of forms. """

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FormDefinition)

    def add(self, title, definition,
            type=None, meta=None, content=None, name=None):
        """ Add the given form to the database. """
        form = FormDefinition()

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

        """
        if with_submissions:
            submissions = self.session.query(FormSubmission)
            submissions = submissions.filter(FormSubmission.name == name)
            submissions.delete()

        self.query().filter(FormDefinition.name == name).delete('fetch')
        self.session.flush()

    def by_name(self, name):
        """ Returns the given form by name or None. """
        return self.query().filter(FormDefinition.name == name).first()


class FormSubmissionCollection(object):
    """ Manages a collection of submissions. """

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FormSubmission)

    def add(self, form_name, form, state):
        """ Takes a form filled-out form instance and stores the submission
        in the database. The form instance is expected to have a ``_source``
        parameter, which contains the source used to build the form (as only
        forms with this source may be stored).

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
        submission.id = uuid4()
        submission.name = form_name
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

    def update(self, submission, form):
        """ Takes a submission and a form and updates the submission data
        as well as the files stored in a spearate table.

        """
        assert submission.id and submission.state

        submission.definition = form._source
        submission.data = form.data

        # pending submissions are not necessarily valid, however we don't need
        # to store invalid state as it is wiped out anyway
        submission.prune(form)

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

    def remove_old_pending_submissions(self, older_than):
        """ Removes all pending submissions older than the given date. The
        date is expected to be in UTC!

        """
        if older_than.tzinfo is None:
            older_than = Delorean(older_than, timezone='UTC').datetime

        query = self.query()

        # delete the ones that were never modified
        query = query.filter(FormSubmission.state == 'pending')
        query = query.filter(FormSubmission.modified == None)
        query = query.filter(FormSubmission.created < older_than)
        query.delete()

        # delete the ones that were modified
        query = query.filter(FormSubmission.state == 'pending')
        query = query.filter(FormSubmission.modified != None)
        query = query.filter(FormSubmission.modified < older_than)
        query.delete()

    def by_form_name(self, name):
        """ Return all submissions for the given form-name. """
        return self.query().filter(FormSubmission.name == name).all()

    def by_id(self, id, state=None):
        """ Return the submission by id. """
        query = self.query().filter(FormSubmission.id == id)

        if state is not None:
            query = query.filter(FormSubmission.state == state)

        return query.first()
