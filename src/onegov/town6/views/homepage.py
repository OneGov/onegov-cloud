from onegov.core.security import Public
from onegov.org.views.homepage import view_org
from onegov.town6 import TownApp
from onegov.org.models import Organisation
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=Organisation, template='homepage.pt', permission=Public)
def town_view_org(self, request):
    return view_org(self, request, DefaultLayout(self, request))
