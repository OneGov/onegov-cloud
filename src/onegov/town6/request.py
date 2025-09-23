from __future__ import annotations

from onegov.org.request import OrgRequest
from functools import cached_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.app import TownApp


# NOTE: Currently this is purely for type checking, so we know the requests
#       in our election day app have the election day app available
class TownRequest(OrgRequest):
    if TYPE_CHECKING:
        app: TownApp

    @cached_property
    def is_parliamentarian(self) -> bool:
        """Check if current user has parliamentarian role."""
        parls = {'parliamentarian', 'commission_president'}
        if not self.current_user:
            return False
        return self.current_user.role in parls
