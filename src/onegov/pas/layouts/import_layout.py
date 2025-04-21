from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.app import TownApp
    from onegov.town6.request import TownRequest


class ImportLayout(DefaultLayout):

    if TYPE_CHECKING:
        app: TownApp
        request: TownRequest

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
