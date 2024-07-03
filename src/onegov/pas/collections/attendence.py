from onegov.core.collection import GenericCollection
from onegov.pas.models import Attendence
from sqlalchemy import desc

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class AttendenceCollection(GenericCollection[Attendence]):

    @property
    def model_class(self) -> type[Attendence]:
        return Attendence

    def query(self) -> 'Query[Attendence]':
        return super().query().order_by(desc(Attendence.date))
