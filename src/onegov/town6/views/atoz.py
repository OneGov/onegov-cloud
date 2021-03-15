from onegov.core.security import Public
from onegov.org.models import AtoZ
from onegov.org.views.atoz import atoz
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def town_atoz(self, request):
    return atoz(self, request, DefaultLayout(self, request))
