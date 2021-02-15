from onegov.core.security import Public
from onegov.org.models import AtoZ
from onegov.org.views.atoz import atoz
from onegov.town import TownApp


@TownApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def town_atoz(self, request):
    return atoz(self, request)
