from __future__ import annotations

from onegov.core.security import Public
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.forms import LandsgemeindeSearchForm
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.org.models import Search
from onegov.org.views.search import search

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.html(model=Search, template='search.pt', permission=Public)
def landsgemeinde_search(
    self: Search,
    request: LandsgemeindeRequest
) -> RenderData | Response:
    return search(
        self,
        request,
        DefaultLayout(self, request),
        LandsgemeindeSearchForm
    )
