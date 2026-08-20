from __future__ import annotations

from onegov.core.security import Private
from onegov.org.models import Organisation
from onegov.org.views.information_architecture import (
    view_information_architecture)
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=Organisation,
    name='information-architecture',
    template='information_architecture.pt',
    permission=Private
)
def town_view_information_architecture(
    self: Organisation,
    request: TownRequest,
    layout: DefaultLayout | None = None
) -> RenderData:
    return view_information_architecture(
        self, request, layout or DefaultLayout(self, request)
    )
