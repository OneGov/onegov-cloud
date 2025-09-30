from __future__ import annotations

from onegov.pas.utils import is_parliamentarian
from functools import cached_property
from onegov.town6.request import TownRequest

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import PASParliamentarian


class PasRequest(TownRequest):

    @cached_property
    def is_parliamentarian(self) -> bool:
        return is_parliamentarian(self.current_user)

    @cached_property
    def current_parliamentarian(self) -> PASParliamentarian | None:
        """Returns the current parliamentarian if user is parliamentarian."""
        if (self.current_user
            and hasattr(self.current_user, 'parliamentarian')
            and self.current_user.parliamentarian):
            return self.current_user.parliamentarian
        return None
