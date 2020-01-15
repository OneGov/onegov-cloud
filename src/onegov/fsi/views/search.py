from onegov.core.security import Personal
from onegov.fsi import FsiApp
from onegov.org.models import Search
from onegov.org.views.search import search as search_view
from onegov.org.views.search import suggestions as suggestions_view


@FsiApp.html(model=Search, template='search.pt', permission=Personal)
def search(self, request):
    return search_view(self, request)


@FsiApp.json(model=Search, name='suggest', permission=Personal)
def suggestions(self, request):
    return suggestions_view(self, request)
