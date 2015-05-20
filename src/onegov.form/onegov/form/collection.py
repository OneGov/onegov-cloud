from onegov.core.utils import normalize_for_url
from onegov.form.models import FormDefinition, FormSubmission


class FormCollection(object):
    """ Manages a collection of forms defined in the database. """

    def __init__(self, session):
        self.session = session

    @property
    def definitions(self):
        return FormDefinitionCollection(self.session)

    @property
    def submissions(self):
        return FormSubmissionCollection(self.session)


class FormDefinitionCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FormDefinition)

    def add(self, title, definition, type=None, meta=None, content=None):
        form = FormDefinition()

        form.name = normalize_for_url(title)
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

    def by_name(self, name):
        return self.query().filter(FormDefinition.name == name).first()


class FormSubmissionCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(FormSubmission)

    def add(self, form_name, form):
        """ Takes a form filled-out form instance and stores the submission
        in the database. The form instance is expected to have a ``_source``
        parameter, which contains the source used to build the form (as only
        forms with this source may be stored).

        """

        assert hasattr(form, '_source')

        # this should happen way earlier, we just double check here
        assert form.validate()

        submission = FormSubmission()
        submission.name = form_name
        submission.definition = form._source
        submission.data = form.data

        self.session.add(submission)
        self.session.flush()

        return submission

    def by_form_name(self, name):
        return self.query().filter(FormSubmission.name == name).all()
