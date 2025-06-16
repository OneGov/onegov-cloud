from __future__ import annotations

from datetime import date
from onegov.core.collection import GenericCollection
from sqlalchemy import or_

from typing import TYPE_CHECKING

from onegov.parliament.models import RISParty, Party

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

    def query(self) -> Query[Party]:
        query = super().query()
        model_class = self.model_class
        if self.active is not None:
            if self.active:
                query = query.filter(
                    or_(
                        self.model_class.end.is_(None),
                        self.model_class.end >= date.today()
                    )
                )
            else:
                query = query.filter(model_class.end < date.today())
        return query.order_by(model_class.name)

    def for_filter(
        self,
        active: bool | None = None
    ) -> Self:
        return self.__class__(self.session, active)


class RISPartyCollection(PartyCollection):

    @property
    def model_class(self) -> type[Party]:
        return RISParty
