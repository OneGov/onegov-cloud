from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import PASCommission
from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class CommissionCollection(GenericCollection[PASCommission]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[PASCommission]:
        return PASCommission

    def query(self) -> Query[PASCommission]:
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        PASCommission.end.is_(None),
                        PASCommission.end >= date.today()
                    )
                )
            else:
                query = query.filter(PASCommission.end < date.today())

        return query.order_by(PASCommission.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
