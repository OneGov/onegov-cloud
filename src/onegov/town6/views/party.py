from __future__ import annotations

from webob.exc import HTTPNotFound

from onegov.core.security import Private, Public

from onegov.parliament.collections import RISPartyCollection
from onegov.parliament.forms.party import PartyForm
from onegov.parliament.models import RISParty
from onegov.parliament.views.party import (
    view_parties,
    add_party,
    view_party,
    edit_party,
    delete_party
)
from onegov.town6.layout import RISPartyCollectionLayout, RISPartyLayout

from onegov.town6 import TownApp

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=RISPartyCollection,
    template='parties.pt',
    permission=Public
)
def ris_view_parties(
    self: RISPartyCollection,
    request: TownRequest
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parties(self, request, RISPartyCollectionLayout(self, request))


@TownApp.form(
    model=RISPartyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def ris_add_party(
    self: RISPartyCollection,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return add_party(
        self,
        request,
        form,
        RISPartyCollectionLayout(self, request)
    )


@TownApp.html(
    model=RISParty,
    template='party.pt',
    permission=Public
)
def ris_view_party(
    self: RISParty,
    request: TownRequest
) -> RenderData:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_party(self, request, RISPartyLayout(self, request))


@TownApp.form(
    model=RISParty,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PartyForm
)
def ris_edit_party(
    self: RISParty,
    request: TownRequest,
    form: PartyForm
) -> RenderData | Response:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return edit_party(self, request, form, RISPartyLayout(self, request))


@TownApp.view(
    model=RISParty,
    request_method='DELETE',
    permission=Private
)
def ris_delete_party(
    self: RISParty,
    request: TownRequest
) -> None:
    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return delete_party(self, request)
