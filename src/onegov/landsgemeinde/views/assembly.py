from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.forms import AssemblyForm
from onegov.landsgemeinde.layouts import AssemblyCollectionLayout
from onegov.landsgemeinde.layouts import AssemblyLayout
from onegov.landsgemeinde.layouts import AssemblyTickerLayout
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.html(
    model=AssemblyCollection,
    template='assemblies.pt',
    permission=Public
)
def view_assemblies(
    self: AssemblyCollection,
    request: 'LandsgemeindeRequest'
) -> 'RenderData':

    layout = AssemblyCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'assemblies': self.query().all(),
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=AssemblyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=AssemblyForm
)
def add_assembly(
    self: AssemblyCollection,
    request: 'LandsgemeindeRequest',
    form: AssemblyForm
) -> 'RenderData | Response':

    if form.submitted(request):
        assembly = self.add(**form.get_useful_data())
        request.success(_("Added a new assembly"))

        return redirect(request.link(assembly))

    layout = AssemblyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New assembly"),
        'form': form,
    }


@LandsgemeindeApp.html(
    model=Assembly,
    template='assembly.pt',
    permission=Public
)
def view_assembly(
    self: Assembly,
    request: 'LandsgemeindeRequest'
) -> 'RenderData | Response':

    layout = AssemblyLayout(self, request)

    if not request.is_manager and layout.current_assembly() == self:
        return redirect(request.link(self, name='ticker'))

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': self.agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.html(
    model=Assembly,
    name='ticker',
    template='ticker.pt',
    permission=Public
)
def view_assembly_ticker(
    self: Assembly,
    request: 'LandsgemeindeRequest'
) -> 'RenderData':

    layout = AssemblyTickerLayout(self, request)

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.view(
    model=Assembly,
    name='ticker',
    request_method='HEAD',
    permission=Public
)
def view_assembly_ticker_head(
    self: Assembly,
    request: 'LandsgemeindeRequest'
) -> None:

    @request.after
    def add_headers(response: 'Response') -> None:
        last_modified = self.last_modified or self.modified or self.created
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            )


@LandsgemeindeApp.html(
    model=Assembly,
    name='states',
    template='states.pt',
    permission=Private
)
def view_assembly_states(
    self: Assembly,
    request: 'LandsgemeindeRequest'
) -> 'RenderData':

    layout = AssemblyLayout(self, request)
    layout.editbar_links = []
    layout.breadcrumbs.append(Link(_("States"), '#'))

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=Assembly,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AssemblyForm
)
def edit_assembly(
    self: Assembly,
    request: 'LandsgemeindeRequest',
    form: AssemblyForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        updated = ensure_states(self)
        updated.add(self)
        update_ticker(request, updated)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = AssemblyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=Assembly,
    request_method='DELETE',
    permission=Private
)
def delete_assembly(self: Assembly, request: 'LandsgemeindeRequest') -> None:

    request.assert_valid_csrf_token()

    collection = AssemblyCollection(request.session)
    collection.delete(self)
