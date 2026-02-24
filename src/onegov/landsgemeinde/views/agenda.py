from __future__ import annotations

from morepath import redirect
from onegov.core.elements import BackLink, Link
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.core.utils import append_query_param
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.forms import AgendaItemForm
from onegov.landsgemeinde.forms.agenda import AgendaItemUploadForm
from onegov.landsgemeinde.layouts import AgendaItemCollectionLayout
from onegov.landsgemeinde.layouts import AgendaItemLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models.agenda import STATES
from onegov.landsgemeinde.utils import ensure_states, timestamp_to_seconds
from onegov.landsgemeinde.utils import update_ticker


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


def get_agenda_item_form_class(
    model: object,
    request: LandsgemeindeRequest
) -> type[AgendaItemForm]:

    if isinstance(model, AgendaItem):
        return model.with_content_extensions(AgendaItemForm, request)
    return AgendaItem().with_content_extensions(AgendaItemForm, request)


@LandsgemeindeApp.form(
    model=AgendaItemCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_agenda_item_form_class
)
def add_agenda_item(
    self: AgendaItemCollection,
    request: LandsgemeindeRequest,
    form: AgendaItemForm
) -> RenderData | Response:

    if form.submitted(request):
        agenda_item = self.add(
            number=form.number.data,
            assembly_id=self.assembly.id,  # type: ignore
            state=form.state.data,
        )
        form.populate_obj(agenda_item)
        updated = ensure_states(agenda_item)
        updated.add(agenda_item.assembly)
        update_ticker(request, updated)
        request.success(_('Added a new agenda item'))

        return redirect(request.link(agenda_item))

    form.number.data = form.next_number

    layout = AgendaItemCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})

    return {
        'layout': layout,
        'title': _('New agenda item'),
        'form': form,
    }


@LandsgemeindeApp.form(
    model=AgendaItemCollection,
    name='new-import',
    template='form.pt',
    permission=Private,
    form=AgendaItemUploadForm
)
def import_agenda_item(
    self: AgendaItemCollection,
    request: LandsgemeindeRequest,
    form: AgendaItemUploadForm
) -> RenderData | Response:

    if form.submitted(request):
        agenda_item = form.import_agenda_item(self)
        request.success(_('Imported a new agenda item'))
        return redirect(request.link(agenda_item, 'edit'))

    layout = AgendaItemCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Import'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': _('New agenda item'),
        'form': form,
    }


@LandsgemeindeApp.html(
    model=AgendaItem,
    template='agenda_item.pt',
    permission=Public
)
def view_agenda_item(
    self: AgendaItem,
    request: LandsgemeindeRequest
) -> RenderData:

    layout = AgendaItemLayout(self, request)
    agenda_items = self.assembly.agenda_items
    video_url = self.video_url
    if video_url and request.params.get('start', ''):
        video_url = video_url.split('&start=')[0]
        video_url = append_query_param(
            video_url, 'start', str(request.params['start']))
        video_url = append_query_param(video_url, 'autoplay', '1')
        video_url = append_query_param(video_url, 'allow', '"autoplay"')
        video_url = append_query_param(video_url, 'mute', '1')
        video_url = append_query_param(video_url, 'rel', '0')

    prev_item = None
    next_item = None

    if agenda_items:
        index = agenda_items.index(self)
        if index > 0:
            prev_item = agenda_items[index - 1]
        if index < len(agenda_items) - 1:
            next_item = agenda_items[index + 1]

    return {
        'layout': layout,
        'agenda_item': self,
        'prev_item': prev_item,
        'next_item': next_item,
        'video_url': video_url,
        'agenda_items': agenda_items,
        'timestamp_to_seconds': timestamp_to_seconds,
        'append_query_param': append_query_param,
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=AgendaItem,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_agenda_item_form_class
)
def edit_agenda_item(
    self: AgendaItem,
    request: LandsgemeindeRequest,
    form: AgendaItemForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        updated = ensure_states(self)
        updated.add(self)
        update_ticker(request, updated)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AgendaItemLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=AgendaItem,
    request_method='DELETE',
    permission=Private
)
def delete_agenda_item(
    self: AgendaItem,
    request: LandsgemeindeRequest
) -> None:

    request.assert_valid_csrf_token()

    update_ticker(request, {self.assembly})  # force refresh

    collection = AgendaItemCollection(request.session)
    collection.delete(self)
    ensure_states(
        self.assembly.agenda_items[-1]
        if self.assembly.agenda_items else self.assembly
    )


@LandsgemeindeApp.view(
    model=AgendaItem,
    name='change-state',
    request_method='POST',
    permission=Private
)
def change_agenda_item_state(
    self: AgendaItem,
    request: LandsgemeindeRequest
) -> str:
    layout = AgendaItemLayout(self, request)
    request.assert_valid_csrf_token()

    i = list(STATES).index(self.state)
    self.state = list(STATES)[(i + 1) % len(STATES)]

    updated = ensure_states(self)
    updated.add(self)
    update_ticker(request, updated)

    assembly = self.assembly
    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(assembly).all()
    )

    return render_macro(
        layout.macros['states-list'],
        request,
        {'assembly': assembly,
         'agenda_items': agenda_items,
         'layout': layout,
         'state': self.state}
    )
