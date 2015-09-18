from onegov.core.security import Public
from onegov.town import _, TownApp
from onegov.town.models import Search
from onegov.town.layout import DefaultLayout


@TownApp.html(model=Search, template='search.pt', permission=Public)
def search(self, request):
    return {
        'title': _("Search Results"),
        'model': self,
        'layout': DefaultLayout(self, request)
    }
