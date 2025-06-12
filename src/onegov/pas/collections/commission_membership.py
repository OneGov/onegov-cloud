from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models import PASCommissionMembership


class CommissionMembershipCollection(
    GenericCollection[PASCommissionMembership]
):

    @property
    def model_class(self) -> type[PASCommissionMembership]:
        return PASCommissionMembership
