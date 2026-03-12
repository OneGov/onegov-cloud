from __future__ import annotations

from onegov.parliament.collections import CommissionMembershipCollection
from onegov.pas.models import PASCommissionMembership


class PASCommissionMembershipCollection(
    CommissionMembershipCollection[PASCommissionMembership]
):

    @property
    def model_class(self) -> type[PASCommissionMembership]:
        return PASCommissionMembership
