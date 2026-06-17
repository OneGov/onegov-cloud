from __future__ import annotations

from onegov.core.request import CoreRequest


from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.app import ElectionDayApp


AppT = TypeVar(
    'AppT',
    bound='ElectionDayApp',
    default='ElectionDayApp',
    covariant=True
)


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
class ElectionDayRequest(CoreRequest[AppT]):
    pass
