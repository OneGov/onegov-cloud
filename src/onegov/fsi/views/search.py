from __future__ import annotations

from onegov.core.security import Personal
from onegov.fsi import FsiApp
from onegov.org.models import Search
from onegov.org.views.search import suggestions
from onegov.town6.views.search import town_search

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro, RenderData
    from onegov.fsi.request import FsiRequest
    from webob import Response


@FsiApp.html(
    model=Search,
    template='search.pt',
    permission=Personal
)
def fsi_search(
    self: Search,
    request: FsiRequest
) -> RenderData | Response:
    return town_search(self, request)


@FsiApp.json(model=Search, name='suggest', permission=Personal)
def fsi_suggestions(
    self: Search,
    request: FsiRequest
) -> JSON_ro:
    return suggestions(self, request)
