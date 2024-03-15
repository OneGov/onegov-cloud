from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PartyCollection
from onegov.pas.forms import PartyForm
from onegov.pas.layouts import PartyCollectionLayout
from onegov.pas.layouts import PartyLayout
from onegov.pas.models import Party

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PartyCollection,
    template='parties.pt',
    permission=Private
)
def view_parties(
    self: PartyCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = PartyCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'parties': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=PartyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def add_party(
    self: PartyCollection,
    request: 'TownRequest',
    form: PartyForm
) -> 'RenderData | Response':

    if form.submitted(request):
        party = self.add(**form.get_useful_data())
        request.success(_("Added a new party"))

        return request.redirect(request.link(party))

    layout = PartyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New party"),
        'form': form,
    }


@PasApp.html(
    model=Party,
    template='party.pt',
    permission=Private
)
def view_party(
    self: Party,
    request: 'TownRequest'
) -> 'RenderData':

    layout = PartyLayout(self, request)

    return {
        'layout': layout,
        'party': self,
        'title': layout.title,
    }


@PasApp.form(
    model=Party,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def edit_party(
    self: Party,
    request: 'TownRequest',
    form: PartyForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = PartyLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []
    layout.include_editor()

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=Party,
    request_method='DELETE',
    permission=Private
)
def delete_party(
    self: Party,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = PartyCollection(request.session)
    collection.delete(self)
