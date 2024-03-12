from onegov.core.security import Public
from onegov.org.views.search import search
from onegov.town6 import TownApp
from onegov.org.models import Search
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import Base
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=Search, template='search.pt', permission=Public)
def town_search(
    self: Search['Base'],
    request: 'TownRequest'
) -> 'RenderData | Response':
    return search(self, request, DefaultLayout(self, request))
