from onegov.core.security import Secret
from onegov.org.views.dashboard import dashboard
from onegov.town6 import TownApp
from onegov.org.models import Dashboard
from onegov.town6.layout import DashboardLayout


@TownApp.html(model=Dashboard, template='dashboard.pt', permission=Secret)
def town_dashboard(self, request):
    return dashboard(self, request, DashboardLayout(self, request))
