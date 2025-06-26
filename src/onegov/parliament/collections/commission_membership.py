from onegov.core.collection import GenericCollection
from onegov.parliament.models.commission_membership import (
    RISCommissionMembership,
    CommissionMembership
)


class CommissionMembershipCollection(GenericCollection[CommissionMembership]):

    pass


class RISCommissionMembershipCollection(CommissionMembershipCollection):

    @property
    def model_class(self) -> type[CommissionMembership]:
        return RISCommissionMembership
