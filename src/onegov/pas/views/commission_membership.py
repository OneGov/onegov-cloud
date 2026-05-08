from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.layouts import PASCommissionMembershipLayout
from onegov.pas.models import PASCommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=PASCommissionMembership,
    template='commission_membership.pt',
    permission=Private
)
def view_commission_membership(
    self: PASCommissionMembership,
    request: TownRequest
) -> RenderData:

    layout = PASCommissionMembershipLayout(self, request)

    return {
        'layout': layout,
        'commission_membership': self,
        'title': layout.title,
    }
