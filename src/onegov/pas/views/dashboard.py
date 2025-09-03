from __future__ import annotations

from datetime import date

from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.layouts import DefaultLayout
from onegov.org.models import Organisation
from onegov.core.security import Personal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.pas.request import PasRequest


@PasApp.html(
    model=Organisation,
    name='pas',
    template='dashboard.pt',
    permission=Personal
)
def view_dashboard(
    self: Organisation,
    request: PasRequest
) -> RenderData:

    layout = DefaultLayout(self, request)
    shortcuts = []
    if request.is_admin:
        shortcuts = [
            {
                'name': 'commissions',
                'title': _('Commissions'),
                'link': request.class_link(PASCommissionCollection),
                'icon': 'fa-user-friends'
            },
            {
                'name': 'pas-import',
                'title': _('Data Import (JSON)'),
                'link': request.link(self, 'pas-import'),
                'icon': 'fa-file-import',
            }
        ]

    if request.is_parliamentarian:
        # For parliamentarians, show only their commissions
        user = request.current_user
        if user and hasattr(user, 'parliamentarian') and user.parliamentarian:
            parliamentarian = user.parliamentarian
            active_memberships = [
                m for m in parliamentarian.commission_memberships
                if not m.end or m.end >= date.today()
            ]
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
        'title': _('Dashboard'),
        'shortcuts': shortcuts
    }
