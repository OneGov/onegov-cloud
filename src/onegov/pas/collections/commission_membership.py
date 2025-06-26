from __future__ import annotations

from onegov.parliament.collections.commission_membership import (
    CommissionMembershipCollection
)
from onegov.parliament.models import CommissionMembership
from onegov.pas.models import PASCommissionMembership


class PASCommissionMembershipCollection(CommissionMembershipCollection):

    @property
    def model_class(self) -> type[PASCommissionMembership]:
        return PASCommissionMembership
