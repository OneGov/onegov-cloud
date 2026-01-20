from __future__ import annotations

from onegov.core.security import Public
from onegov.org.models import AtoZ
from onegov.org.views.atoz import atoz
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(model=AtoZ, template='atoz.pt', permission=Public)
def town_atoz(self: AtoZ[Any], request: TownRequest) -> RenderData:
    return atoz(self, request, DefaultLayout(self, request))
