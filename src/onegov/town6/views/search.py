from onegov.core.security import Public
from onegov.org.views.search import search
from onegov.town6 import _, TownApp
from onegov.org.models import Search


@TownApp.html(model=Search, template='search.pt', permission=Public)
def town_search(self, request):
    return search(self, request)
