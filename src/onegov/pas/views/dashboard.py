from __future__ import annotations

from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PASCommissionCollection
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
    template='pas_dashboard.pt',
    permission=Private
)
def view_dashboard(
    self: Organisation,
    request: TownRequest
) -> RenderData:

    layout = DefaultLayout(self, request)

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

    return {
        'layout': layout,
        'title': _('Overview'),
        'shortcuts': shortcuts
    }
