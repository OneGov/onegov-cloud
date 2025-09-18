from __future__ import annotations

from onegov.pas.utils import is_parliamentarian
from functools import cached_property
from onegov.town6.request import TownRequest


class PasRequest(TownRequest):

    @cached_property
    def is_parliamentarian(self) -> bool:
        return is_parliamentarian(self.current_user)
