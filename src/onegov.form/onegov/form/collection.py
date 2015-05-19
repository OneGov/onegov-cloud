from onegov.forms.models import FormDefinition, FormSubmission


class FormCollection(object):
    """ Manages a collection of forms defined in the database. """

    def __init__(self, session):
        self.session = session

    def definitions(self):
        return self.session.query(FormDefinition)

    def submissions(self):
        return self.session.query(FormSubmission)

    def get_definition(self, name, revision):
        query = self.definitions()
        query = query.filter(FormDefinition.name == name)
        query = query.filter(FormDefinition.revision == revision)

        return query.first()
