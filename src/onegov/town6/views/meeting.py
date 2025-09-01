from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import morepath
import os
import zipfile

from webob.exc import HTTPNotFound
from webob.response import Response

from onegov.core.elements import Link
from onegov.core.security.permissions import Public, Private
from onegov.org.forms import MeetingForm
from onegov.org.forms.meeting import MeetingExportPoliticalBusinessForm

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


@TownApp.form(
    model=Meeting,
    permission=Public,
    name='export',
    template='export.pt',
    form=MeetingExportPoliticalBusinessForm,
    pass_model=True
)
def view_meeting_export(
    self: Meeting,
    request: TownRequest,
    form: MeetingExportPoliticalBusinessForm
) -> RenderData | Response:

    def build_zip_response() -> Response:
        meeting_doc_ids = form.get_selected_meeting_documents_ids()
        agenda_item_doc_ids = form.get_selected_agenda_item_document_ids()

        base_storage_path = request.app.depot_storage_path
        assert (base_storage_path is not None), (
            'Depot storage path is not configured')

        with (NamedTemporaryFile(delete=False) as f):
            zip_path = f.name

            with zipfile.ZipFile(
                    zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # meeting documents
                for file in self.files:
                    if file.id in meeting_doc_ids:
                        path = (
                                Path(base_storage_path)
                                / file.reference.path / 'file')
                        with open(path, 'rb') as file_content:
                            zip_file.writestr(
                                os.path.join(self.display_name, file.name),
                                file_content.read())

                # agenda item documents
                for meeting_item in self.meeting_items:
                    business = meeting_item.political_business
                    if business:
                        for file in business.files:
                            if file.id in agenda_item_doc_ids:
                                path = (
                                        Path(base_storage_path)
                                        / file.reference.path / 'file')
                                with open(path, 'rb') as file_content:
                                    zip_file.writestr(
                                        os.path.join(
                                            meeting_item.title, file.name),
                                        file_content.read())

            with open(zip_path, 'rb') as zip_file:
                response = Response()
                response.body = zip_file.read()
                response.content_type = 'application/zip'
                response.content_disposition = (
                    f'attachment; filename="{self.display_name}.zip"')
                return response

    # layout = MeetingCollectionLayout(self, request)
    layout = MeetingLayout(self, request)
    layout.breadcrumbs.append(Link(_('Export'), '#'))
    layout.editbar_links = None

    file_count = 0
    file_count += len(self.files)
    for meeting_item in self.meeting_items:
        if meeting_item.political_business:
            file_count += len(meeting_item.political_business.files)

    if form.submitted(request):
        form.populate_obj(self)
        return build_zip_response()

    meeting_items_no_docs = []
    if not self.files:
        meeting_items_no_docs.append(self.display_name)
    for meeting_item in self.meeting_items:
        if not meeting_item.political_business:
            meeting_items_no_docs.append(meeting_item.title)
        else:
            if not meeting_item.political_business.files:
                meeting_items_no_docs.append(meeting_item.title)

    return {
        'layout': layout,
        'form': form,
        'title': _('Export meeting documents'),
        'explanation': _('Select the meeting documents and agenda item '
                         'documents you want to export. The resulting zipfile '
                         'contains the documents per meeting item.'),
        'has_note': True if meeting_items_no_docs else False,
        'note': 'Please note that not documents are assigned to the following '
                'agenda items: {}'.format(
            ', '.join(meeting_items_no_docs) if meeting_items_no_docs else ''),
        'filters': None,
        'count': file_count,
    }
