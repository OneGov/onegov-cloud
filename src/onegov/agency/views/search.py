from __future__ import annotations

from onegov.agency import AgencyApp
from onegov.agency.layout import AgencySearchLayout
from onegov.core.security import Public
from onegov.org.models import Search, SearchPostgres
from onegov.org.views.search import search as search_view, search_postgres

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.orm import Base
    from onegov.core.types import RenderData
    from webob import Response


@AgencyApp.html(model=Search, template='search.pt', permission=Public)
def search(
    self: Search[Base],
    request: AgencyRequest
) -> RenderData | Response:

    data = search_view(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data


@AgencyApp.html(model=SearchPostgres, template='search_postgres.pt',
                permission=Public)
def agency_search_postgres(
    self: SearchPostgres[Base],
    request: AgencyRequest
) -> RenderData | Response:
    data = search_postgres(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data
