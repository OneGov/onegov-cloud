from cached_property import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


class InvoiceLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Create invoice")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def cancel_url(self):
        return self.invoices_url

    @cached_property
    def success_url(self):
        return self.invoices_url
