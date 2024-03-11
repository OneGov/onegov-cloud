from onegov.core.collection import GenericCollection
from onegov.pas.models import Party

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class PartyCollection(GenericCollection[Party]):

    @property
    def model_class(self) -> type[Party]:
        return Party

    def query(self) -> 'Query[Party]':
        return super().query().order_by(Party.name)
