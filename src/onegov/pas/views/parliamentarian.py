from __future__ import annotations

from onegov.core.security import Private
from onegov.parliament.views import (
    add_commission_membership,
    add_parliamentarian,
    delete_parliamentarian,
    edit_parliamentarian,
    view_parliamentarian,
    view_parliamentarians,
)
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.forms import PASParliamentarianForm
from onegov.pas.forms import ParliamentarianRoleForm
from onegov.pas.layouts import PASParliamentarianCollectionLayout
from onegov.pas.layouts import PASParliamentarianLayout
from onegov.pas.models import PASParliamentarian

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Private
)
def pas_view_parliamentarians(
    self: PASParliamentarianCollection,
    request: TownRequest
) -> RenderData | Response:

    layout = PASParliamentarianCollectionLayout(self, request)
    return view_parliamentarians(self, request, layout)


@PasApp.form(
    model=PASParliamentarianCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PASParliamentarianForm
)
def pas_add_parliamentarian(
    self: PASParliamentarianCollection,
    request: TownRequest,
    form: PASParliamentarianForm
) -> RenderData | Response:
    layout = PASParliamentarianCollectionLayout(self, request)
    return add_parliamentarian(self, request, form, layout)


@PasApp.html(
    model=PASParliamentarian,
    template='parliamentarian.pt',
    permission=Private
)
def pas_view_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest
) -> RenderData | Response:
    layout = PASParliamentarianLayout(self, request)
    return view_parliamentarian(self, request, layout)


@PasApp.form(
    model=PASParliamentarian,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PASParliamentarianForm
)
def pas_edit_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest,
    form: PASParliamentarianForm
) -> RenderData | Response:
    layout = PASParliamentarianLayout(self, request)
    return edit_parliamentarian(self, request, form, layout)


@PasApp.view(
    model=PASParliamentarian,
    request_method='DELETE',
    permission=Private
)
def pas_delete_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest
) -> None:

    return delete_parliamentarian(self, request)


@PasApp.form(
    model=PASParliamentarian,
    name='new-role',
    template='form.pt',
    permission=Private,
    form=ParliamentarianRoleForm
)
def pas_add_commission_membership(
    self: PASParliamentarian,
    request: TownRequest,
    form: ParliamentarianRoleForm
) -> RenderData | Response:

    layout = PASParliamentarianLayout(self, request)
    return add_commission_membership(self, request, form, layout)
