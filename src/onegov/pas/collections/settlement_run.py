from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import SettlementRun
from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing_extensions import Self


class SettlementRunCollection(GenericCollection[SettlementRun]):

    def __init__(
        self,
        session: 'Session',
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[SettlementRun]:
        return SettlementRun

    def query(self) -> 'Query[SettlementRun]':
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        SettlementRun.end.is_(None),
                        SettlementRun.end >= date.today()
                    )
                )
            else:
                query = query.filter(SettlementRun.end < date.today())

        return query.order_by(SettlementRun.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> 'Self':
        return self.__class__(self.session, active)
