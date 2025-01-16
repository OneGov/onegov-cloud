from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.pas.models import ParliamentaryGroup
from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class ParliamentaryGroupCollection(GenericCollection[ParliamentaryGroup]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[ParliamentaryGroup]:
        return ParliamentaryGroup

    def query(self) -> Query[ParliamentaryGroup]:
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        ParliamentaryGroup.end.is_(None),
                        ParliamentaryGroup.end >= date.today()
                    )
                )
            else:
                query = query.filter(ParliamentaryGroup.end < date.today())

        return query.order_by(ParliamentaryGroup.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
