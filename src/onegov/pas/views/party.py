from __future__ import annotations

from onegov.core.security import Private
from onegov.parliament.views.party import (
    add_party,
    delete_party,
    edit_party,
    view_parties,
    view_party,
)
from onegov.pas import PasApp
from onegov.pas.collections import PASPartyCollection
from onegov.pas.forms import PartyForm
from onegov.pas.layouts import PASPartyCollectionLayout
from onegov.pas.layouts import PASPartyLayout
from onegov.pas.models import PASParty

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASPartyCollection,
    template='parties.pt',
    permission=Private
)
def pas_view_parties(
    self: PASPartyCollection,
    request: TownRequest
) -> RenderData:
    return view_parties(self, request, PASPartyCollectionLayout(self, request))


@PasApp.form(
    model=PASPartyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def pas_add_party(
    self: PASPartyCollection,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:
    return add_party(
        self,
        request,
        form,
        PASPartyCollectionLayout(self, request)
    )


@PasApp.html(
    model=PASParty,
    template='party.pt',
    permission=Private
)
def pas_view_party(
    self: PASParty,
    request: TownRequest
) -> RenderData:
    return view_party(self, request, PASPartyLayout(self, request))


@PasApp.form(
    model=PASParty,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def pas_edit_party(
    self: PASParty,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:

    return edit_party(self, request, form, PASPartyLayout(self, request))


@PasApp.view(
    model=PASParty,
    request_method='DELETE',
    permission=Private
)
def pas_delete_party(
    self: PASParty,
    request: TownRequest
) -> None:

    return delete_party(self, request)
