from cached_property import cached_property

from onegov.core.templates import render_macro
from onegov.form import FormSubmissionCollection
from onegov.ticket import Ticket, Handler, handlers
from onegov.town import _
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from purl import URL


class FormSubmissionTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    @cached_property
    def collection(self):
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self):
        return self.collection.by_id(self.id)

    @cached_property
    def form(self):
        return self.submission.form_class(data=self.submission.data)

    @property
    def email(self):
        return self.submission.email

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

        edit_link = URL(request.link(self.submission))
        edit_link = edit_link.query_param('edit', '')
        edit_link = edit_link.query_param('return-to', request.url)

        return [
            Link(
                text=_('Edit submission'),
                url=edit_link.as_string(),
                classes=('edit-link', )
            )
        ]
