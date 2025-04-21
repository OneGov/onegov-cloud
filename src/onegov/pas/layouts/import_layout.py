from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.request import PasRequest
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


# Add new layout classes for Import Log views
from onegov.pas.collections import ImportLogCollection
from onegov.pas.models import ImportLog


class ImportLogCollectionLayout(DefaultLayout):
    model: ImportLogCollection

    def __init__(
        self, model: ImportLogCollection, request: PasRequest
    ) -> None:
        super().__init__(model, request)
        # Assuming the main import view is the parent conceptually
        self.breadcrumb.append(Link(_('Import'), self.request.link(self.model.__class__, 'pas-import')))
        self.breadcrumb.append(Link(_('Import History'), '#'))  # Current page

    @cached_property
    def collection_url(self) -> str:
        return self.request.link(self.model)


class ImportLogLayout(DefaultLayout):
    model: ImportLog

    def __init__(
        self, model: ImportLog, request: PasRequest
    ) -> None:
        super().__init__(model, request)
        logs_collection = ImportLogCollection(request.session)
        # Link back to the main import view first
        self.breadcrumb.append(Link(_('Import'), self.request.link(self.model.__class__, 'pas-import')))
        # Then link to the history list
        logs_link = request.link(logs_collection)
        self.breadcrumb.append(Link(_('Import History'), logs_link))
        self.breadcrumb.append(Link(_('Details'), '#'))  # Current page

    @cached_property
    def log_url(self) -> str:
        return self.request.link(self.model)
