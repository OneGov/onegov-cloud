from onegov.core.security import Public
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.feriennet import FeriennetApp
from onegov.feriennet.layout import HomepageLayout


@FeriennetApp.html(
    model=Organisation, template='homepage.pt', permission=Public
)
def feriennet_view_org(self, request):
    return view_org(self, request, HomepageLayout(self, request))
