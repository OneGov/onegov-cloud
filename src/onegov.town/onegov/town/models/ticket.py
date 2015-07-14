from cached_property import cached_property

from onegov.core.templates import render_macro
from onegov.form import FormSubmissionCollection
from onegov.ticket import Ticket, Handler, handlers
from onegov.town import _
from onegov.town.layout import DefaultLayout


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

    @cached_property
    def form(self):
        return self.submission.form_class(data=self.submission.data)

    @property
    def title(self):
        return self.submission.title

    @property
    def group(self):
        return self.submission.form.title

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)
        return render_macro(layout.macros['display_form'], request, {
            'form': self.form,
            'layout': layout
        })

    def get_links(self, request):
        return [
            (_("Edit Submission"), request.link(self.submission) + '?edit'),
        ]
