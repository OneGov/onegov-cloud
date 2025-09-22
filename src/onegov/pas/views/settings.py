from __future__ import annotations

from onegov.core.security import Personal
from onegov.org.models import Organisation
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections.parliamentary_group import (
    PASParliamentaryGroupCollection
)
from onegov.pas.layouts import DefaultLayout
from onegov.pas.utils import get_active_commission_memberships


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=Organisation,
    name='pas-settings',
    template='dashboard.pt',
    permission=Personal
)
def view_pas_settings(
    self: Organisation,
    request: TownRequest
) -> RenderData:

    layout = DefaultLayout(self, request)
    shortcuts = []

    if request.is_admin:
        # Admin users see all management options
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
                'link': request.link(request.app.org, 'import'),
                'icon': 'fa-file-import'
            },
        ]

    if request.is_parliamentarian:
        # Add view attendances shortcut for parliamentarians
        shortcuts.append({
            'name': 'view-attendances',
            'title': _('Attendances'),
            'link': request.class_link(AttendenceCollection),
            'icon': 'fa-calendar-check'
        })

        # Add create attendance shortcut for parliamentarians
        shortcuts.append({
            'name': 'create-attendance',
            'title': _('Create Attendance'),
            'link': request.class_link(AttendenceCollection, name='new'),
            'icon': 'fa-plus-circle'
        })

        # For parliamentarians, show their specific commissions
        user = request.current_user
        active_memberships = get_active_commission_memberships(user)
        for membership in active_memberships:
            commission = membership.commission
            shortcuts.append({
                'name': f'commission-{commission.id}',
                'title': commission.name,
                'link': request.link(commission),
                'icon': 'fa-user-friends'
            })

    return {
        'layout': layout,
        'title': _('PAS settings'),
        'shortcuts': shortcuts
    }
