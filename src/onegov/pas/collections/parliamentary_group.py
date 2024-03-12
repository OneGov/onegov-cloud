from onegov.core.collection import GenericCollection
from onegov.pas.models import ParliamentaryGroup

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class ParliamentaryGroupCollection(GenericCollection[ParliamentaryGroup]):

    @property
    def model_class(self) -> type[ParliamentaryGroup]:
        return ParliamentaryGroup

    def query(self) -> 'Query[ParliamentaryGroup]':
        return super().query().order_by(ParliamentaryGroup.name)
