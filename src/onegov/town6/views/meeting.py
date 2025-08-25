from __future__ import annotations

import morepath
from webob.exc import HTTPNotFound

from onegov.core.elements import Link
from onegov.core.security.permissions import Public, Private
from onegov.org.forms import MeetingForm

from onegov.org.models import Meeting
from onegov.org.models import MeetingCollection
from onegov.org.models import MeetingItem
from onegov.org.models import PoliticalBusiness
from onegov.org.models.political_business import POLITICAL_BUSINESS_TYPE
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import MeetingCollectionLayout
from onegov.town6.layout import MeetingLayout

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData
    from onegov.core.request import CoreRequest
    from webob import Response


def get_meeting_form_class(
    model: object,
    request: TownRequest
) -> type[MeetingForm]:

    if isinstance(model, Meeting):
        return model.with_content_extensions(MeetingForm, request)
    return Meeting(title='title').with_content_extensions(
        MeetingForm, request
    )


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
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    filters = {}
    filters['past'] = [
        Link(
            text=request.translate(title),
            active=self.past == value,
            url=request.link(self.for_filter(past=value))
        ) for title, value in (
            (_('Past Meetings'), True),
            (_('Upcoming Meetings'), False)
        )
    ]

    upcoming_meeting = (
        MeetingCollection(request.session, past=False)
        .query()
        .order_by(Meeting.past)
        .first()
    )

    return {
        'filters': filters,
        'layout': layout or MeetingCollectionLayout(self, request),
        'meetings': self.query().all(),
        'upcoming_meeting': upcoming_meeting,
        'past_title': self.past,
        'title': _('Meetings'),
    }


@TownApp.form(
    model=MeetingCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=MeetingForm
)
def add_meeting(
    self: MeetingCollection,
    request: TownRequest,
    form: MeetingForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    layout = MeetingCollectionLayout(self, request)

    if form.submitted(request):
        meeting = self.add(**form.get_useful_data())
        request.success(_('Added a new meeting'))
        return request.redirect(request.link(meeting))

    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'form': form,
        'title': _('New meeting'),
        'form_width': 'large'
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

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    layout = MeetingLayout(self, request)
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
            'business_type': None,
            'political_business_link': None
        }

        if item.political_business_link_id:
            business = request.session.query(PoliticalBusiness).filter(
                PoliticalBusiness.meta['self_id'].astext ==
                item.political_business_link_id
            ).first()
            if business is not None:
                item_data['political_business_link'] = request.link(business)
                item_data['business_type'] = (
                    POLITICAL_BUSINESS_TYPE)[business.political_business_type]
        else:
            if item.political_business:
                item_data['political_business_link'] = (
                    request.link(item.political_business))
                item_data['business_type'] = (
                    POLITICAL_BUSINESS_TYPE)[item.political_business.political_business_type]

        meeting_items_with_links.append(item_data)

    meeting_items_with_links.sort(
        key=lambda x: (x['number'] or '', x['title'] or '')
    )

    links = []
    audio_link = self.content.get('audio_link', None)
    if audio_link:
        links.append(('Parlamentsdebatte anhören', audio_link))
    video_link = self.content.get('video_link', None)
    if video_link:
        links.append(('Parlamentsdebatte ansehen', video_link))

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
        'sidepanel_links': links,
    }


@TownApp.form(
    model=Meeting,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_meeting_form_class,
    pass_model=True
)
def edit_meeting(
    self: Meeting,
    request: TownRequest,
    form: MeetingForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    layout = MeetingLayout(self, request)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.include_editor()
    layout.editbar_links = []
    layout.edit_mode = True

    return {
        'layout': layout,
        'form': form,
        'title': _('Edit meeting'),
        'form_width': 'full'
    }


@TownApp.view(
    model=Meeting,
    request_method='DELETE',
    permission=Private
)
def delete_meeting(
    self: Meeting,
    request: TownRequest
) -> None:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    request.assert_valid_csrf_token()

    collection = MeetingCollection(request.session)
    collection.delete(self)

    request.success(_('The meeting has been deleted.'))


@TownApp.view(model=MeetingItem, permission=Public)
def view_redirect_meeting_item_to_meeting(
    self: MeetingItem, request: CoreRequest
) -> Response:
    """
    Redirect for search results, if we link to MeetingItem we show the Meeting
    """
    return morepath.redirect(request.link(self.meeting))
