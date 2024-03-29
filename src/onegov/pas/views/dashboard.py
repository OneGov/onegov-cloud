from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import ParliamentarianCollection
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
            'name': 'attendences',
            'title': _('Attendences'),
            'link': request.class_link(AttendenceCollection),
            'icon': 'fa-clock'
        },
        {
            'name': 'parliamentarians',
            'title': _('Parliamentarians'),
            'link': request.class_link(ParliamentarianCollection),
            'icon': 'fa-user-tie'
        },
        {
            'name': 'commissions',
            'title': _('Commissions'),
            'link': request.class_link(CommissionCollection),
            'icon': 'fa-user-friends'
        }
    ]

    return {
        'layout': layout,
        'title': _("Dashboard"),
        'shortcuts': shortcuts
    }
