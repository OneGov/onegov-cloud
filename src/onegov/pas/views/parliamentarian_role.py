from __future__ import annotations

from onegov.core.security import Private
from onegov.town6.views.parliamentarian_role import (
    view_parliamentarian_role,
)
from onegov.pas import PasApp
from onegov.pas.layouts import PASParliamentarianRoleLayout
from onegov.pas.models import PASParliamentarianRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASParliamentarianRole,
    template='parliamentarian_role.pt',
    permission=Private
)
def pas_view_parliamentarian_role(
    self: PASParliamentarianRole,
    request: TownRequest
) -> RenderData | Response:

    layout = PASParliamentarianRoleLayout(self, request)
    return view_parliamentarian_role(self, request, layout)
