from onegov.core.collection import GenericCollection
from onegov.pas.models import LegislativePeriod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query


class LegislativePeriodCollection(GenericCollection[LegislativePeriod]):

    @property
    def model_class(self) -> type[LegislativePeriod]:
        return LegislativePeriod

    def query(self) -> 'Query[LegislativePeriod]':
        return super().query().order_by(LegislativePeriod.name)
