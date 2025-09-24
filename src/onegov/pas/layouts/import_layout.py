from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.layouts import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.app import PasApp
    from onegov.pas.request import PasRequest


class ImportLayout(DefaultLayout):

    if TYPE_CHECKING:
        app: PasApp
        request: PasRequest

    @cached_property
    def title(self) -> str:
        return 'Import'

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('JSON Import'),
                self.request.link(self.model, 'pas-import'),
            ),
        ]
