from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import CommissionMembership


class CommissionMembershipCollection(GenericCollection[CommissionMembership]):

    @property
    def model_class(self) -> type[CommissionMembership]:
        return CommissionMembership
