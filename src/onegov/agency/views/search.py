from __future__ import annotations

from onegov.agency import AgencyApp
from onegov.agency.layout import AgencySearchLayout
from onegov.core.security import Public
from onegov.org.models import Search
from onegov.org.views.search import search as search_view

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response


@AgencyApp.html(model=Search, template='search.pt', permission=Public)
def search(
    self: Search,
    request: AgencyRequest
) -> RenderData | Response:

    data = search_view(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data
