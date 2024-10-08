from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import CommissionCollection
from onegov.pas.layouts import DefaultLayout
from onegov.org.models import Organisation
from onegov.core.security import Private


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=Organisation,
    name='pas',
    template='dashboard.pt',
    permission=Private
)
def view_dashboard(
    self: Organisation,
    request: 'TownRequest'
) -> 'RenderData':
    layout = DefaultLayout(self, request)

    shortcuts = [
        {
            'name': 'commissions',
            'title': _('Commissions'),
            'link': request.class_link(CommissionCollection),
            'icon': 'fa-user-friends'
        }
    ]

    return {
        'layout': layout,
        'title': _('Dashboard'),
        'shortcuts': shortcuts
    }
