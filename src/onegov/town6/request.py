from __future__ import annotations

from onegov.org.request import OrgRequest


from typing import TYPE_CHECKING, TypeVar
if TYPE_CHECKING:
    from onegov.town6.app import TownApp


AppT = TypeVar('AppT', bound='TownApp', default='TownApp', covariant=True)


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our town app have the town app available
class TownRequest(OrgRequest[AppT]):
    pass
