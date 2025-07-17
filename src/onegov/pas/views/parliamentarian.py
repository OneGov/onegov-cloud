from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.forms import PASParliamentarianForm
from onegov.pas.forms import PASParliamentarianRoleForm
from onegov.pas.layouts import PASParliamentarianCollectionLayout
from onegov.pas.layouts import PASParliamentarianLayout
from onegov.pas.models import PASParliamentarian
from onegov.town6.views.parliamentarian import add_commission_membership
from onegov.town6.views.parliamentarian import add_parliamentarian
from onegov.town6.views.parliamentarian import delete_parliamentarian
from onegov.town6.views.parliamentarian import edit_parliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarians

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
    form=PASParliamentarianRoleForm
)
def pas_add_commission_membership(
    self: PASParliamentarian,
    request: TownRequest,
    form: PASParliamentarianRoleForm
) -> RenderData | Response:

    layout = PASParliamentarianLayout(self, request)
    return add_commission_membership(self, request, form, layout)
