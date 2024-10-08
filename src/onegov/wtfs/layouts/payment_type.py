from functools import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element


class PaymentTypesLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Manage payment types')

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def cancel_url(self) -> str:
        return self.invoices_url

    @cached_property
    def success_url(self) -> str:
        return self.invoices_url
