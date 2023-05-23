from onegov.core.security import Public
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.org.models import Search
from onegov.org.views.search import search


@LandsgemeindeApp.html(model=Search, template='search.pt', permission=Public)
def landsgemeinde_search(self, request):
    return search(self, request, DefaultLayout(self, request))
