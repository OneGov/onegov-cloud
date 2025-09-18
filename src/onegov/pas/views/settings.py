from __future__ import annotations

from onegov.core.security import Private
from onegov.org.models import Organisation
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections.parliamentary_group import (
    PASParliamentaryGroupCollection
)
from onegov.pas.layouts import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=Organisation,
    name='pas-settings',
    template='pas_dashboard.pt',
    permission=Private
)
def view_pas_settings(
    self: Organisation,
    request: TownRequest
) -> RenderData:

    layout = DefaultLayout(self, request)

    shortcuts = [
        {
            'name': 'attendences',
            'title': _('Attendences'),
            'link': request.class_link(AttendenceCollection),
            'icon': 'fa-clock'
        },
        {
            'name': 'rate-sets',
            'title': _('Rate sets'),
            'link': request.class_link(RateSetCollection),
            'icon': 'fa-exchange-alt'
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
            'link': request.class_link(PASParliamentaryGroupCollection),
            'icon': 'fa-handshake'
        },
        {
            'name': 'commissions',
            'title': _('Commissions'),
            'link': request.class_link(PASCommissionCollection),
            'icon': 'fa-user-friends'
        },
        {
            'name': 'parliamentarians',
            'title': _('Parliamentarians'),
            'link': request.class_link(PASParliamentarianCollection),
            'icon': 'fa-user-tie'
        },
        {
            'name': 'import',
            'title': _('Data Import (JSON)'),
            'link': request.link(request.app.org, 'pas-import'),
            'icon': 'fa-file-import'
        },
    ]

    return {
        'layout': layout,
        'title': _('PAS settings'),
        'shortcuts': shortcuts
    }
