from __future__ import annotations

from onegov.parliament.collections import CommissionCollection
from onegov.pas.models import PASCommission


class PASCommissionCollection(CommissionCollection):

    @property
    def model_class(self) -> type[PASCommission]:
        return PASCommission
