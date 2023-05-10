from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.forms import AgendaItemForm
from onegov.landsgemeinde.layouts import AgendaItemCollectionLayout
from onegov.landsgemeinde.layouts import AgendaItemLayout
from onegov.landsgemeinde.models import AgendaItem


@LandsgemeindeApp.html(
    model=AgendaItemCollection,
    template='agenda_items.pt',
    permission=Private
)
def view_agenda_items(self, request):

    layout = AgendaItemCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'agenda_items': self.query().all(),
        'title': layout.title,
    }


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
        request.success(_("Added a new agenda item"))

        return redirect(request.link(agenda_item))

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
    permission=Private
)
def view_agenda_item(self, request):

    layout = AgendaItemLayout(self, request)

    return {
        'layout': layout,
        'agenda_item': self,
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

    collection = AgendaItemCollection(request.session)
    collection.delete(self)
