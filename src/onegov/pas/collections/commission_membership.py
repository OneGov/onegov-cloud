from onegov.core.collection import GenericCollection
from onegov.pas.models import CommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class CommissionMembershipCollection(GenericCollection[CommissionMembership]):

    @property
    def model_class(self) -> type[CommissionMembership]:
        return CommissionMembership

    def query(self) -> 'Query[CommissionMembership]':
        return super().query()
