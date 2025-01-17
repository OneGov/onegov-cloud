from __future__ import annotations

from onegov.org.request import OrgRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.app import TownApp


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
class TownRequest(OrgRequest):
    if TYPE_CHECKING:
        app: TownApp
