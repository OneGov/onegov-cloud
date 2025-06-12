from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import RateSet

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class RateSetCollection(GenericCollection[RateSet]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[RateSet]:
        return RateSet

    def query(self) -> Query[RateSet]:
        query = super().query()

        if self.active is not None:
            year = date.today().year
            if self.active:
                query = query.filter(RateSet.year == year)
            else:
                query = query.filter(RateSet.year != year)

        return query.order_by(RateSet.year.desc())

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
