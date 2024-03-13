from onegov.core.collection import GenericCollection
from onegov.pas.models import Commission

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class CommissionCollection(GenericCollection[Commission]):

    @property
    def model_class(self) -> type[Commission]:
        return Commission

    def query(self) -> 'Query[Commission]':
        return super().query().order_by(Commission.name)
