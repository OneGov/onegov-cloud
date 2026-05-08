from __future__ import annotations

from onegov.pas.i18n import _
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
    def is_commission_president(self) -> bool:
        user = self.current_user
        if not user:
            return False
        return user.role == 'commission_president'

    @cached_property
    def current_parliamentarian(self) -> PASParliamentarian | None:
        if (self.current_user
            and hasattr(self.current_user, 'parliamentarian')
            and self.current_user.parliamentarian):
            return self.current_user.parliamentarian
        return None

    def warn_no_parliamentarian(self) -> bool:
        if (
            self.current_user
            and self.current_user.role
            in ('parliamentarian', 'commission_president')
            and not self.current_parliamentarian
        ):
            self.warning(
                _(
                    'Your user account is not linked '
                    'to a parliamentarian record. '
                    'Please contact an administrator.'
                )
            )
            return True
        return False
