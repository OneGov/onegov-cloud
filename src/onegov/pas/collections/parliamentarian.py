from onegov.core.collection import GenericCollection
from onegov.pas.models import Parliamentarian

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class ParliamentarianCollection(GenericCollection[Parliamentarian]):

    @property
    def model_class(self) -> type[Parliamentarian]:
        return Parliamentarian

    def query(self) -> 'Query[Parliamentarian]':
        return super().query().order_by(
            Parliamentarian.last_name,
            Parliamentarian.first_name
        )
