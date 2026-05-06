from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.layouts import PASParliamentarianCollectionLayout
from onegov.pas.layouts import PASParliamentarianLayout
from onegov.pas.models import PASParliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarians


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Private
)
def pas_view_parliamentarians(
    self: PASParliamentarianCollection,
    request: TownRequest
) -> RenderData | Response:
    layout = PASParliamentarianCollectionLayout(self, request)
    return view_parliamentarians(self, request, layout)


@PasApp.html(
    model=PASParliamentarian,
    template='parliamentarian.pt',
    permission=Private
)
def pas_view_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest
) -> RenderData | Response:
    layout = PASParliamentarianLayout(self, request)
    return view_parliamentarian(self, request, layout)
