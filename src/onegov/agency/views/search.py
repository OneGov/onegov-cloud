from onegov.agency import AgencyApp
from onegov.agency.layout import AgencySearchLayout
from onegov.core.security import Public
from onegov.org.models import Search
from onegov.org.views.search import search as search_view
from onegov.org.views.search import suggestions as suggestions_view


@AgencyApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):
    data = search_view(self, request)
    if isinstance(data, dict):
        data['layout'] = AgencySearchLayout(self, request)
    return data


@AgencyApp.json(model=Search, name='suggest', permission=Public)
def suggestions(self, request):
    return suggestions_view(self, request)
