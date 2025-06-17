from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.pas.models import PASParliamentarian

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import Self


class ParliamentarianCollection(GenericCollection[PASParliamentarian]):

    def __init__(
        self,
        session: Session,
        active: bool | None = None
    ):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[PASParliamentarian]:
        return PASParliamentarian

    def query(self) -> Query[PASParliamentarian]:

        query = super().query()

        if self.active is not None:
            id_query = self.session.query(PASParliamentarian)
            if self.active:
                ids = [p.id for p in id_query if p.active]
                query = query.filter(PASParliamentarian.id.in_(ids))
            else:
                ids = [p.id for p in id_query if not p.active]
                query = query.filter(PASParliamentarian.id.in_(ids))

        return query.order_by(
            PASParliamentarian.last_name,
            PASParliamentarian.first_name
        ).distinct()

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)
