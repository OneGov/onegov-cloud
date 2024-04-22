from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import CostOfLivingAdjustment

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing_extensions import Self


class CostOfLivingAdjustmentCollection(
    GenericCollection[CostOfLivingAdjustment]
):

    def __init__(
        self,
        session: 'Session',
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[CostOfLivingAdjustment]:
        return CostOfLivingAdjustment

    def query(self) -> 'Query[CostOfLivingAdjustment]':
        query = super().query()

        if self.active is not None:
            year = date.today().year
            if self.active:
                query = query.filter(CostOfLivingAdjustment.year == year)
            else:
                query = query.filter(CostOfLivingAdjustment.year != year)

        return query.order_by(CostOfLivingAdjustment.year.desc())

    def for_filter(
        self,
        active: bool | None = None
    ) -> 'Self':
        return self.__class__(self.session, active)
