from __future__ import annotations


from onegov.core.security.permissions import Public
from onegov.parliament import _

from onegov.parliament.collections import MeetingCollection
from onegov.parliament.models import Meeting
from onegov.town6.layout import MeetingCollectionLayout

from onegov.town6 import TownApp

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData


@TownApp.html(
    model=MeetingCollection,
    template='meetings.pt',
    permission=Public,
)
def view_meetings(
    self: MeetingCollection,
    request: TownRequest,
    layout: MeetingCollectionLayout | None = None
) -> RenderData:

    return {
        'layout': layout or MeetingCollectionLayout(self, request),
        'meetings': self.query().all(),
        'title': _('Meetings'),
    }


@TownApp.html(
    model=Meeting,
    template='meeting.pt',
    permission=Public,
)
def view_meeting(
    self: Meeting,
    request: TownRequest,
) -> RenderData:

    collection = MeetingCollection(request.session)
    layout = MeetingCollectionLayout(collection, request)
    return {
        'layout': layout,
        'page': self,
        'text': '',
        'lead': '',
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': None,
        'title': self.title,
    }
