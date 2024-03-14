from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.forms import ParliamentarianForm
from onegov.pas.layouts import ParliamentarianCollectionLayout
from onegov.pas.layouts import ParliamentarianLayout
from onegov.pas.models import Parliamentarian

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=ParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Private
)
def view_parliamentarians(
    self: ParliamentarianCollection,
    request: 'TownRequest'
) -> 'RenderData':

    layout = ParliamentarianCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'parliamentarians': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=ParliamentarianCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ParliamentarianForm
)
def add_parliamentarian(
    self: ParliamentarianCollection,
    request: 'TownRequest',
    form: ParliamentarianForm
) -> 'RenderData | Response':

    if form.submitted(request):
        parliamentarian = self.add(**form.get_useful_data())
        request.success(_("Added a new parliamentarian"))

        return request.redirect(request.link(parliamentarian))

    layout = ParliamentarianCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _("New parliamentarian"),
        'form': form,
    }


@PasApp.html(
    model=Parliamentarian,
    template='parliamentarian.pt',
    permission=Private
)
def view_parliamentarian(
    self: Parliamentarian,
    request: 'TownRequest'
) -> 'RenderData':

    layout = ParliamentarianLayout(self, request)

    return {
        'layout': layout,
        'parliamentarian': self,
        'title': layout.title,
    }


@PasApp.form(
    model=Parliamentarian,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentarianForm
)
def edit_parliamentarian(
    self: Parliamentarian,
    request: 'TownRequest',
    form: ParliamentarianForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = ParliamentarianLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=Parliamentarian,
    request_method='DELETE',
    permission=Private
)
def delete_parliamentarian(
    self: Parliamentarian,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentarianCollection(request.session)
    collection.delete(self)
