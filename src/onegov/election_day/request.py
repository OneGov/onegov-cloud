from __future__ import annotations

from onegov.core.request import CoreRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.app import ElectionDayApp


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
class ElectionDayRequest(CoreRequest):
    if TYPE_CHECKING:
        app: ElectionDayApp
