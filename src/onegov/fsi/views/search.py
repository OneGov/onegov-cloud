from __future__ import annotations

from onegov.core.security import Personal
from onegov.fsi import FsiApp
from onegov.fsi.layout import DefaultLayout
from onegov.org.models import Search, SearchPostgres
from onegov.org.views.search import (search, search_postgres,
                                     suggestions, suggestions_postgres)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from onegov.core.types import JSON_ro, RenderData
    from onegov.fsi.request import FsiRequest
    from webob import Response


@FsiApp.html(
    model=Search,
    template='search.pt',
    permission=Personal
)
def fsi_search(
    self: Search[Base],
    request: FsiRequest
) -> RenderData | Response:
    return search(self, request, DefaultLayout(self, request))


@FsiApp.html(
    model=SearchPostgres,
    template='search_postgres.pt',
    permission=Personal
)
def fsi_search_postgres(
    self: SearchPostgres[Base],
    request: FsiRequest
) -> RenderData | Response:
    return search_postgres(self, request, DefaultLayout(self, request))


@FsiApp.json(model=Search, name='suggest', permission=Personal)
def fsi_suggestions(
    self: Search[Base],
    request: FsiRequest
) -> JSON_ro:
    return suggestions(self, request)


@FsiApp.json(model=SearchPostgres, name='suggest', permission=Personal)
def fsi_suggestions_postgres(
    self: SearchPostgres[Base],
    request: FsiRequest
) -> JSON_ro:
    return suggestions_postgres(self, request)
