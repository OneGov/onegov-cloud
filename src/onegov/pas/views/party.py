from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PartyCollection
from onegov.pas.layouts import PartyCollectionLayout
from onegov.pas.layouts import PartyLayout
from onegov.pas.models import Party

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=PartyCollection,
    template='parties.pt',
    permission=Private
)
def pas_view_parties(
    self: PartyCollection,
    request: TownRequest
) -> RenderData:
    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    layout = PartyCollectionLayout(self, request)
    return {
        'filters': filters,
        'layout': layout,
        'parties': self.query().all(),
        'title': layout.title,
    }


@PasApp.html(
    model=Party,
    template='party.pt',
    permission=Private
)
def pas_view_party(
    self: Party,
    request: TownRequest
) -> RenderData:

    layout = PartyLayout(self, request)
    return {
        'layout': layout,
        'party': self,
        'title': layout.title,
    }
