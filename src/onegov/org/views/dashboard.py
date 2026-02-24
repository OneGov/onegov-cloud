from __future__ import annotations

from onegov.core.security import Public, Secret
from onegov.org import _, OrgApp
from onegov.org.layout import DashboardLayout
from onegov.org.models import CitizenDashboard, Dashboard
from onegov.org.views.utils import assert_citizen_logged_in


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(model=Dashboard, template='dashboard.pt', permission=Secret)
def dashboard(
    self: Dashboard,
    request: OrgRequest,
    layout: DashboardLayout | None = None
) -> RenderData:
    """
    The dashboard shows all the `Boardlet`s that are assigned to the
    dashboard.
    For org and town: `/org/boardlets.py`

    """
    layout = layout or DashboardLayout(self, request)
    return {
        'title': _('Overview'),
        'model': self,
        'layout': layout
    }


@OrgApp.html(
    model=CitizenDashboard,
    template='dashboard.pt',
    permission=Public
)
def citizen_dashboard(
    self: CitizenDashboard,
    request: OrgRequest,
    layout: DashboardLayout | None = None
) -> RenderData:
    """
    The dashboard shows all the `Boardlet`s that are assigned to the
    citizen dashboard.
    For org and town: `/org/boardlets.py`

    """
    assert_citizen_logged_in(request)

    layout = layout or DashboardLayout(self, request)
    return {
        'title': _('Overview'),
        'model': self,
        'layout': layout
    }
