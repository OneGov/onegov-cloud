from onegov.core.security import Personal
from onegov.fsi import FsiApp
from onegov.org.models import Search, SearchPostgres
from onegov.org.views.search import search as search_view
from onegov.org.views.search import search_postgres as search_postgres_view
from onegov.org.views.search import suggestions as suggestions_view
from onegov.org.views.search import (suggestions_postgres as
                                     suggestions_postgres_view)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from onegov.core.types import JSON_ro, RenderData
    from onegov.fsi.request import FsiRequest
    from webob import Response


@FsiApp.html(model=Search, template='search.pt', permission=Personal)
def search(
    self: Search['Base'],
    request: 'FsiRequest'
) -> 'RenderData | Response':
    return search_view(self, request)


@FsiApp.html(model=SearchPostgres, template='search.pt', permission=Personal)
def search_postgres(
    self: SearchPostgres['Base'],
    request: 'FsiRequest'
) -> 'RenderData | Response':
    return search_postgres_view(self, request)


@FsiApp.json(model=Search, name='suggest', permission=Personal)
def suggestions(
    self: Search['Base'],
    request: 'FsiRequest'
) -> 'JSON_ro':
    return suggestions_view(self, request)


@FsiApp.json(model=SearchPostgres, name='suggest', permission=Personal)
def suggestions_postgres(
    self: SearchPostgres['Base'],
    request: 'FsiRequest'
) -> 'JSON_ro':
    return suggestions_postgres_view(self, request)
