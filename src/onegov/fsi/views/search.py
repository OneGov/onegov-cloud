from onegov.core.security import Personal
from onegov.fsi import FsiApp
from onegov.org.models import Search
from onegov.org.views.search import search as search_view
from onegov.org.views.search import suggestions as suggestions_view


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


@FsiApp.json(model=Search, name='suggest', permission=Personal)
def suggestions(
    self: Search['Base'],
    request: 'FsiRequest'
) -> 'JSON_ro':
    return suggestions_view(self, request)
