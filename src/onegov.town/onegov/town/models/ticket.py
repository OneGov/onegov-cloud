from cached_property import cached_property

from onegov.ticket import Ticket, Handler, handlers
from onegov.form import FormSubmissionCollection


class FormSubmissionTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    @cached_property
    def collection(self):
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self):
        return self.collection.by_id(self.data['submission_id'])

    @property
    def title(self):
        return self.submission.title

    @property
    def group(self):
        return self.submission.form.title
