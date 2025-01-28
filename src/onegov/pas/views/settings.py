from __future__ import annotations

from onegov.core.security import Private
from onegov.core.security import Secret
from onegov.org.models import Organisation
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.layouts import DefaultLayout
from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=Organisation,
    name='pas-settings',
    template='dashboard.pt',
    permission=Private
)
def view_settings(
    self: Organisation,
    request: TownRequest
) -> RenderData:
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
            'name': 'settlement-runs',
            'title': _('Settlement runs'),
            'link': request.class_link(SettlementRunCollection),
            'icon': 'fa-hand-holding-usd'
        },
        {
            'name': 'parties',
            'title': _('Parties'),
            'link': request.class_link(PartyCollection),
            'icon': 'fa-users'
        },
        {
            'name': 'parliamentary-groups',
            'title': _('Parliamentary groups'),
            'link': request.class_link(ParliamentaryGroupCollection),
            'icon': 'fa-handshake'
        },
        {
            'name': 'commissions',
            'title': _('Commissions'),
            'link': request.class_link(CommissionCollection),
            'icon': 'fa-user-friends'
        },
        {
            'name': 'parliamentarians',
            'title': _('Parliamentarians'),
            'link': request.class_link(ParliamentarianCollection),
            'icon': 'fa-user-tie'
        },
    ]

    return {
        'layout': layout,
        'title': _('PAS settings'),
        'shortcuts': shortcuts
    }


@PasApp.view(
    model=Organisation,
    name='user-settings',
    permission=Secret,
    setting=_('Usermanagement'),
    icon='fa-user',
    order=-1200
)
def handle_chat_settings(
    self: Organisation,
    request: TownRequest,
) -> Response:
    return request.redirect(request.class_link(UserCollection))
