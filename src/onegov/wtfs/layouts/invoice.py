from functools import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.layouts.default import DefaultLayout
from onegov.wtfs.security import EditModel


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element


class InvoiceLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _("Create invoice")

    @cached_property
    def editbar_links(self) -> list['Element']:
        result: list[Element] = []
        model = PaymentTypeCollection(self.request.session)
        if self.request.has_permission(model, EditModel):
            result.append(
                Link(
                    text=_("Manage payment types"),
                    url=self.request.link(model),
                    attrs={'class': 'payment-icon'}
                )
            )
        return result

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.invoices_url

    @cached_property
    def success_url(self) -> str:
        return self.invoices_url
