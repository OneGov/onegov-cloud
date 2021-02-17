from onegov.core.security import Public
from onegov.org.views.search import search
from onegov.town6 import TownApp
from onegov.org.models import Search
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=Search, template='search.pt', permission=Public)
def town_search(self, request):
    return search(self, request, DefaultLayout(self, request))
