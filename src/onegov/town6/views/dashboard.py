from onegov.core.security import Secret
from onegov.org.views.dashboard import dashboard
from onegov.town6 import TownApp
from onegov.org.models import Dashboard
from onegov.town6.layout import DashboardLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(model=Dashboard, template='dashboard.pt', permission=Secret)
def town_dashboard(self: Dashboard, request: 'TownRequest') -> 'RenderData':
    return dashboard(self, request, DashboardLayout(self, request))
