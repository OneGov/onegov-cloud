from __future__ import annotations

from webob.exc import HTTPNotFound

from onegov.core.security import Private
from onegov.org.models import Organisation
from onegov.parliament.collections import PoliticalBusinessCollection
from onegov.parliament.collections import MeetingCollection
from onegov.parliament.collections import RISCommissionCollection
from onegov.parliament.collections.parliamentarian import (
    RISParliamentarianCollection
)
from onegov.parliament.collections.parliamentary_group import (
    RISParliamentaryGroupCollection
)
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout
from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=Organisation,
    name='ris-settings',
    template='ris_settings.pt',
    permission=Private
)
def view_ris_settings(
    self: Organisation,
    request: TownRequest
) -> RenderData:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    layout = DefaultLayout(self, request)

    shortcuts = [
        {
            'name': 'parliamentarians',
            'title': _('Parliamentarians'),
            'link': request.class_link(RISParliamentarianCollection),
            'icon': 'fa-user-tie'
        },
        {
            'name': 'parliamentary-groups',
            'title': _('Parliamentary groups'),
            'link': request.class_link(RISParliamentaryGroupCollection),
            'icon': 'fa-handshake'
        },
        {
            'name': 'commissions',
            'title': _('Commissions'),
            'link': request.class_link(RISCommissionCollection),
            'icon': 'fa-user-friends'
        },
        {
            'name': 'meetings',
            'title': _('Meetings'),
            'link': request.class_link(MeetingCollection),
            'icon': 'fa-chair'
        },
        {
            'name': 'political-businesses',
            'title': _('Political Businesses'),
            'link': request.class_link(PoliticalBusinessCollection),
            'icon': 'fa-file-contract'
        },
        # delegations
    ]

    return {
        'layout': layout,
        'title': _('RIS Settings'),
        'shortcuts': shortcuts
    }
