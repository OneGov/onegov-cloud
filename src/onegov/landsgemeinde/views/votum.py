from __future__ import annotations

from morepath import redirect
from onegov.core.elements import BackLink, Link
from onegov.core.security import Private
from onegov.core.templates import render_macro
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import (AgendaItemCollection,
                                              VotumCollection)
from onegov.landsgemeinde.forms import VotumForm
from onegov.landsgemeinde.layouts import VotumCollectionLayout
from onegov.landsgemeinde.layouts import VotumLayout
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker
from onegov.landsgemeinde.models.votum import STATES


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


@LandsgemeindeApp.form(
    model=VotumCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=VotumForm
)
def add_votum(
    self: VotumCollection,
    request: LandsgemeindeRequest,
    form: VotumForm
) -> RenderData | Response:

    if form.submitted(request):
        votum = self.add(**form.get_useful_data())
        updated = ensure_states(votum)
        updated.add(votum)
        update_ticker(request, updated)
        request.success(_('Added a new votum'))

        return redirect(
            request.link(votum.agenda_item, fragment=f'votum-{votum.number}'),
        )

    form.number.data = form.next_number

    layout = VotumCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})

    return {
        'layout': layout,
        'title': _('New votum'),
        'form': form,
    }


@LandsgemeindeApp.form(
    model=Votum,
    name='edit',
    template='form.pt',
    permission=Private,
    form=VotumForm
)
def edit_votum(
    self: Votum,
    request: LandsgemeindeRequest,
    form: VotumForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        updated = ensure_states(self)
        updated.add(self)
        update_ticker(request, updated)
        request.success(_('Your changes were saved'))
        return request.redirect(
            request.link(self.agenda_item, fragment=f'votum-{self.number}')
        )

    form.process(obj=self)

    layout = VotumLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=Votum,
    request_method='DELETE',
    permission=Private
)
def delete_votum(self: Votum, request: LandsgemeindeRequest) -> None:

    request.assert_valid_csrf_token()

    collection = VotumCollection(request.session)
    collection.delete(self)
    ensure_states(
        self.agenda_item.vota[-1]
        if self.agenda_item.vota else self.agenda_item
    )

    update_ticker(request, {self.agenda_item})


@LandsgemeindeApp.view(
    model=Votum,
    name='change-state',
    request_method='POST',
    permission=Private
)
def change_votum_state(
    self: Votum,
    request: LandsgemeindeRequest
) -> str:
    layout = VotumLayout(self, request)
    request.assert_valid_csrf_token()

    i = list(STATES).index(self.state)
    self.state = list(STATES)[(i + 1) % len(STATES)]

    updated = ensure_states(self)
    updated.add(self)
    update_ticker(request, updated)

    assembly = self.agenda_item.assembly
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
