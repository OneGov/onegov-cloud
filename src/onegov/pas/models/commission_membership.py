from __future__ import annotations

from onegov.parliament.models import CommissionMembership


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


class PASCommissionMembership(CommissionMembership):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_commission_membership',
    }

    def is_active_on(self, on_date: date) -> bool:
        return (self.start is None or self.start <= on_date) and (
            self.end is None or self.end >= on_date
        )
