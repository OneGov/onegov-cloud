from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.parliament.collections import RISParliamentarianCollection
from onegov.parliament.forms import ParliamentarianForm
from onegov.parliament.forms import ParliamentarianRoleForm
from onegov.parliament.models import RISParliamentarian
from onegov.parliament.views import (
    add_commission_membership,
    delete_parliamentarian,
    edit_parliamentarian,
    view_parliamentarian,
    add_parliamentarian,
    view_parliamentarians
)
from onegov.town6 import TownApp
from onegov.town6.layout import (
    RISParliamentarianCollectionLayout,
    RISParliamentarianLayout
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=RISParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Public
)
def ris_view_parliamentarians(
    self: RISParliamentarianCollection,
    request: TownRequest
) -> RenderData | Response:

    layout = RISParliamentarianCollectionLayout(self, request)
    return view_parliamentarians(self, request, layout)


@TownApp.form(
    model=RISParliamentarianCollection,
    name='new',
    template='form.pt',
    permission=Public,
    form=ParliamentarianForm
)
def ris_add_parliamentarian(
    self: RISParliamentarianCollection,
    request: TownRequest,
    form: ParliamentarianForm
) -> RenderData | Response:

    layout = RISParliamentarianCollectionLayout(self, request)
    return add_parliamentarian(self, request, form, layout)


@TownApp.html(
    model=RISParliamentarian,
    template='parliamentarian.pt',
    permission=Public
)
def ris_view_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return view_parliamentarian(self, request, layout)


@TownApp.form(
    model=RISParliamentarian,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentarianForm
)
def ris_edit_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest,
    form: ParliamentarianForm
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return edit_parliamentarian(self, request, form, layout)


@TownApp.view(
    model=RISParliamentarian,
    request_method='DELETE',
    permission=Private
)
def ris_delete_parliamentarian(
    self: RISParliamentarian,
    request: TownRequest
) -> None:

    return delete_parliamentarian(self, request)


@TownApp.form(
    model=RISParliamentarian,
    name='new-role',
    template='form.pt',
    permission=Private,
    form=ParliamentarianRoleForm
)
def ris_add_commission_membership(
    self: RISParliamentarian,
    request: TownRequest,
    form: ParliamentarianRoleForm
) -> RenderData | Response:

    layout = RISParliamentarianLayout(self, request)
    return add_commission_membership(self, request, form, layout)
