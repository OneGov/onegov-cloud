from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from onegov.parliament.models import Party
from sqlalchemy import or_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class PartyCollection(GenericCollection[Party]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[Party]:
        return Party

    def query(self) -> Query[Party]:
        query = super().query()

        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        Party.end.is_(None),
                        Party.end >= date.today()
                    )
                )
            else:
                query = query.filter(Party.end < date.today())

        return query.order_by(Party.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
