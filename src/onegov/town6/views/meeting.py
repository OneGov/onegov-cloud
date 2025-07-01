from __future__ import annotations

import morepath

from onegov.core.security.permissions import Public

from onegov.parliament.collections import MeetingCollection
from onegov.parliament.models import Meeting
from onegov.parliament.models.meeting_item import MeetingItem
from onegov.parliament.models.political_business import PoliticalBusiness
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import MeetingCollectionLayout

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData
    from onegov.core.request import CoreRequest
    from webob import Response


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
    title = (
        self.title + ' - ' + layout.format_date(self.start_datetime, 'date')
        if self.start_datetime
        else self.title
    )

    # Construct meeting items with political business links
    meeting_items_with_links = []
    for item in self.meeting_items or []:
        item_data = {
            'number': item.number,
            'title': item.title,
            'political_business_link': None
        }
        if item.political_business_link_id:
            business = request.session.query(PoliticalBusiness).filter(
                PoliticalBusiness.meta['self_id'].astext ==
                item.political_business_link_id
            ).first()
            if business is not None:
                item_data['political_business_link'] = request.link(business)
        meeting_items_with_links.append(item_data)

    return {
        'layout': layout,
        'page': self,
        'text': '',
        'lead': '',
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': None,
        'title': title,
        'meeting_items_with_links': meeting_items_with_links,
    }


@TownApp.view(model=MeetingItem, permission=Public)
def view_redirect_meeting_item_to_meeting(
        self: MeetingItem, request: CoreRequest
) -> Response:
    """
    Redirect for search results, if we link to MeetingItem we show the Meeting
    """
    return morepath.redirect(request.link(self.meeting))
