from __future__ import annotations

from onegov.core.security import Public
from onegov.org.views.publications import view_publications
from onegov.town6 import TownApp
from onegov.org.models import PublicationCollection
from onegov.town6.layout import PublicationLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=PublicationCollection,
    permission=Public,
    template='publications.pt'
)
def town_view_publications(
    self: PublicationCollection,
    request: TownRequest
) -> RenderData:
    return view_publications(self, request, PublicationLayout(self, request))
