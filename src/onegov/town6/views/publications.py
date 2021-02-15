from onegov.core.security import Public
from onegov.org.views.publications import view_publications
from onegov.town6 import TownApp
from onegov.org.models import PublicationCollection


@TownApp.html(model=PublicationCollection, permission=Public,
              template='publications.pt')
def town_view_publications(self, request):
    return view_publications(self, request)
