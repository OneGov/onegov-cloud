from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import PASParliamentaryGroupCollection
from onegov.pas.layouts import PASParliamentaryGroupCollectionLayout
from onegov.pas.layouts import PASParliamentaryGroupLayout
from onegov.pas.models import PASParliamentaryGroup
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
