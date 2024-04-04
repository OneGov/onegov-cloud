from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.forms import AgendaItemForm
from onegov.landsgemeinde.layouts import AgendaItemCollectionLayout
from onegov.landsgemeinde.layouts import AgendaItemLayout
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.form(
    model=AgendaItemCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AgendaItemForm
)
def add_agenda_item(
    self: AgendaItemCollection,
    request: 'LandsgemeindeRequest',
    form: AgendaItemForm
) -> 'RenderData | Response':

    if form.submitted(request):
        agenda_item = self.add(**form.get_useful_data())
        updated = ensure_states(agenda_item)
        updated.add(agenda_item.assembly)
        update_ticker(request, updated)
        request.success(_("Added a new agenda item"))

        return redirect(request.link(agenda_item))

    form.number.data = form.next_number

    layout = AgendaItemCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New agenda item"),
        'form': form,
    }


@LandsgemeindeApp.html(
    model=AgendaItem,
    template='agenda_item.pt',
    permission=Public
)
def view_agenda_item(
    self: AgendaItem,
    request: 'LandsgemeindeRequest'
) -> 'RenderData':

    layout = AgendaItemLayout(self, request)
    agenda_items = self.assembly.agenda_items

    return {
        'layout': layout,
        'agenda_item': self,
        'agenda_items': agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=AgendaItem,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AgendaItemForm
)
def edit_agenda_item(
    self: AgendaItem,
    request: 'LandsgemeindeRequest',
    form: AgendaItemForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        updated = ensure_states(self)
        updated.add(self)
        update_ticker(request, updated)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AgendaItemLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

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
    request: 'LandsgemeindeRequest'
) -> None:

    request.assert_valid_csrf_token()

    update_ticker(request, {self.assembly})  # force refresh

    collection = AgendaItemCollection(request.session)
    collection.delete(self)
    ensure_states(
        self.assembly.agenda_items[-1]
        if self.assembly.agenda_items else self.assembly
    )
