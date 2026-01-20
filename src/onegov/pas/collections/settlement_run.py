from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models import SettlementRun

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class SettlementRunCollection(GenericCollection[SettlementRun]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[SettlementRun]:
        return SettlementRun

    def query(self) -> Query[SettlementRun]:
        query = super().query()

        if self.active is not None:
            query = query.filter(SettlementRun.active.is_(self.active))

        return query.order_by(SettlementRun.start.desc())

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
