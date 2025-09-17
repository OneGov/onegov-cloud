from __future__ import annotations

from functools import cached_property
from onegov.town6.request import TownRequest


class PasRequest(TownRequest):

    @cached_property
    def is_parliamentarian(self) -> bool:
        parls = {'parliamentarian', 'commission_president'}
        if not self.current_user:
            return False
        if self.current_user.role in parls:
            return True
        return False
