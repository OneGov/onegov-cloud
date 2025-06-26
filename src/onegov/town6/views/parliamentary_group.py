from __future__ import annotations

from webob.exc import HTTPNotFound

from onegov.core.security import Public, Private
from onegov.parliament.collections.parliamentary_group import (
    RISParliamentaryGroupCollection,
    RISParliamentaryGroup
)
from onegov.parliament.forms.parliamentary_group import ParliamentaryGroupForm
from onegov.parliament.views.parliamentary_group import (
    view_parliamentary_groups,
    add_parliamentary_group,
    view_parliamentary_group,
    edit_parliamentary_group,
    delete_parliamentary_group,
)
from onegov.town6 import TownApp
from onegov.town6.layout import (
    RISParliamentaryGroupCollectionLayout,
    RISParliamentaryGroupLayout
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webob.response import Response

    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData


@TownApp.html(
    model=RISParliamentaryGroupCollection,
    template='parliamentary_groups.pt',
    permission=Public
)
def ris_view_parliamentary_groups(
    self: RISParliamentaryGroupCollection,
    request: TownRequest
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parliamentary_groups(
        self, request, RISParliamentaryGroupCollectionLayout(self, request)
    )


@TownApp.form(
    model=RISParliamentaryGroupCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def ris_add_parliamentary_group(
    self: RISParliamentaryGroupCollection,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return add_parliamentary_group(
        self,
        request,
        form,
        RISParliamentaryGroupCollectionLayout(self, request)
    )


@TownApp.html(
    model=RISParliamentaryGroup,
    template='parliamentary_group.pt',
    permission=Public
)
def ris_view_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return view_parliamentary_group(
        self, request, RISParliamentaryGroupLayout(self, request)
    )


@TownApp.form(
    model=RISParliamentaryGroup,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def ris_edit_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return edit_parliamentary_group(
        self, request, form, RISParliamentaryGroupLayout(self, request)
    )


@TownApp.view(
    model=RISParliamentaryGroup,
    request_method='DELETE',
    permission=Private
)
def ris_delete_parliamentary_group(
    self: RISParliamentaryGroup,
    request: TownRequest
) -> None:

    if not request.app.org.ris_enabled:
        raise HTTPNotFound()

    return delete_parliamentary_group(self, request)
