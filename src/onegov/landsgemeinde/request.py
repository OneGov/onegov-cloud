from __future__ import annotations

from onegov.town6.request import TownRequest


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.app import LandsgemeindeApp


AppT = TypeVar(
    'AppT',
    bound='LandsgemeindeApp',
    default='LandsgemeindeApp',
    covariant=True
)


# NOTE: Currently this is purely for type checking
#       so we get the correct app on the request
class LandsgemeindeRequest(TownRequest[AppT]):
    pass
