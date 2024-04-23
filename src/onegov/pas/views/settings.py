from onegov.core.security import Private
from onegov.org.models import Organisation
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.layouts import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=Organisation,
    name='pas-settings',
    template='dashboard.pt',
    permission=Private
)
def view_settings(
    self: Organisation,
    request: 'TownRequest'
) -> 'RenderData':
    layout = DefaultLayout(self, request)

    shortcuts = [
        {
            'name': 'rate-sets',
            'title': _('Rate sets'),
            'link': request.class_link(RateSetCollection),
            'icon': 'fa-exchange-alt'
        },
        {
            'name': 'legislative-periods',
            'title': _('Legislative periods'),
            'link': request.class_link(LegislativePeriodCollection),
            'icon': 'fa-calendar-alt'
        },
        {
            'name': 'parliamentary-groups',
            'title': _('Parliamentary groups'),
            'link': request.class_link(ParliamentaryGroupCollection),
            'icon': 'fa-handshake'
        },
        {
            'name': 'parties',
            'title': _('Parties'),
            'link': request.class_link(PartyCollection),
            'icon': 'fa-users'
        },
    ]

    return {
        'layout': layout,
        'title': _("PAS settings"),
        'shortcuts': shortcuts
    }
