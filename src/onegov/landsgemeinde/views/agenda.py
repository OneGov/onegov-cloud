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


@LandsgemeindeApp.form(
    model=AgendaItemCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AgendaItemForm
)
def add_agenda_item(self, request, form):

    if form.submitted(request):
        agenda_item = self.add(**form.get_useful_data())
        ensure_states(agenda_item)
        update_ticker(
            request,
            agenda_item.assembly,
            action='refresh'
        )
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
def view_agenda_item(self, request):

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
def edit_agenda_item(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        ensure_states(self)
        update_ticker(
            request,
            self.assembly,
            agenda_item=self,
            action='update'
        )
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
def delete_agenda_item(self, request):

    request.assert_valid_csrf_token()

    update_ticker(
        request,
        self.assembly,
        action='refresh'
    )

    collection = AgendaItemCollection(request.session)
    collection.delete(self)
    ensure_states(
        self.assembly.agenda_items[-1]
        if self.assembly.agenda_items else self.assembly
    )
