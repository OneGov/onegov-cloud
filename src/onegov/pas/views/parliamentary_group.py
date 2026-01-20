from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentaryGroupCollection
from onegov.pas.forms import ParliamentaryGroupForm
from onegov.pas.layouts import PASParliamentaryGroupCollectionLayout
from onegov.pas.layouts import PASParliamentaryGroupLayout
from onegov.pas.models import PASParliamentaryGroup

from onegov.town6.views.parliamentary_group import add_parliamentary_group
from onegov.town6.views.parliamentary_group import delete_parliamentary_group
from onegov.town6.views.parliamentary_group import edit_parliamentary_group
from onegov.town6.views.parliamentary_group import view_parliamentary_group
from onegov.town6.views.parliamentary_group import view_parliamentary_groups


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response

    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=PASParliamentaryGroupCollection,
    template='parliamentary_groups.pt',
    permission=Private
)
def pas_view_parliamentary_groups(
    self: PASParliamentaryGroupCollection,
    request: TownRequest
) -> RenderData | Response:

    return view_parliamentary_groups(
        self, request, PASParliamentaryGroupCollectionLayout(self, request)
    )


@PasApp.form(
    model=PASParliamentaryGroupCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def pas_add_parliamentary_group(
    self: PASParliamentaryGroupCollection,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    return add_parliamentary_group(
        self,
        request,
        form,
        PASParliamentaryGroupCollectionLayout(self, request)
    )


@PasApp.html(
    model=PASParliamentaryGroup,
    template='parliamentary_group.pt',
    permission=Private
)
def pas_view_parliamentary_group(
    self: PASParliamentaryGroup,
    request: TownRequest
) -> RenderData | Response:

    return view_parliamentary_group(
        self, request, PASParliamentaryGroupLayout(self, request))


@PasApp.form(
    model=PASParliamentaryGroup,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def pas_edit_parliamentary_group(
    self: PASParliamentaryGroup,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    return edit_parliamentary_group(
        self, request, form, PASParliamentaryGroupLayout(self, request))


@PasApp.view(
    model=PASParliamentaryGroup,
    request_method='DELETE',
    permission=Private
)
def pas_delete_parliamentary_group(
    self: PASParliamentaryGroup,
    request: TownRequest
) -> None:

    return delete_parliamentary_group(self, request)
