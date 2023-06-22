from onegov.core.security import Public
from onegov.org.views.search import search, search_postgres
from onegov.town6 import TownApp
from onegov.org.models import Search, SearchPostgres
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=Search, template='search.pt', permission=Public)
def town_search(self, request):
    print('*** tschupre town search')
    return search(self, request, DefaultLayout(self, request))


@TownApp.html(model=SearchPostgres, template='search_postgres.pt',
              permission=Public)
def town_search_postgres(self, request):
    print('*** tschupre town search postgres')
    return search_postgres(self, request, DefaultLayout(self, request))
