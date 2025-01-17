from __future__ import annotations

from onegov.core.security import Public
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.org.models import Search, SearchPostgres
from onegov.org.views.search import search, search_postgres

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.html(model=Search, template='search.pt', permission=Public)
def landsgemeinde_search(
    self: Search[Base],
    request: LandsgemeindeRequest
) -> RenderData | Response:
    return search(self, request, DefaultLayout(self, request))


@LandsgemeindeApp.html(model=SearchPostgres, template='search_postgres.pt',
                       permission=Public)
def landsgemeinde_search_postgres(
    self: SearchPostgres[Base],
    request: LandsgemeindeRequest
) -> RenderData | Response:
    return search_postgres(self, request, DefaultLayout(self, request))
