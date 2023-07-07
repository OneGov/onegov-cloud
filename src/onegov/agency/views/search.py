from onegov.agency import AgencyApp
from onegov.agency.layout import AgencySearchLayout
from onegov.core.security import Public
from onegov.org.models import Search, SearchPostgres
from onegov.org.views.search import search as search_view
from onegov.org.views.search import search_postgres as search_postgres_view


@AgencyApp.html(model=Search, template='search.pt', permission=Public)
def agency_search(self, request):
    data = search_view(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data


@AgencyApp.html(model=SearchPostgres, template='search_postgres.pt',
                permission=Public)
def agency_search_postgres(self, request):
    data = search_postgres_view(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data
