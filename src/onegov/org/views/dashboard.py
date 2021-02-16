from onegov.core.security import Secret
from onegov.org import _, OrgApp
from onegov.org.layout import DashboardLayout
from onegov.org.models import Dashboard


@OrgApp.html(model=Dashboard, template='dashboard.pt', permission=Secret)
def dashboard(self, request, layout=None):
    layout = layout or DashboardLayout(self, request)

    return {
        'title': _("Dashboard"),
        'model': self,
        'layout': layout
    }
