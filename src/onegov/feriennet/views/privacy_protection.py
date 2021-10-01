from onegov.core.security import Public
from onegov.feriennet.app import FeriennetApp
from onegov.feriennet.layout import DefaultLayout
from onegov.org.models import Organisation


@FeriennetApp.html(
    model=Organisation,
    name='privacy-protection',
    template='privacy_protection.pt',
    permission=Public
)
def view_privacy_protection(self, request):
    layout = DefaultLayout(self, request)
    return {
        'layout': layout,
    }
