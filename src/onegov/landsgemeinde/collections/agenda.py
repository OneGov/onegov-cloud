from __future__ import annotations

from functools import cached_property
from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import defaultload
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import undefer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from uuid import UUID


class AgendaItemCollection(GenericCollection[AgendaItem]):

    def __init__(self, session: Session, date: date | None = None) -> None:
        self.session = session
        self.date = date

    @property
    def model_class(self) -> type[AgendaItem]:
        return AgendaItem

    def query(self) -> Query[AgendaItem]:
        query = super().query()
        if self.date:
            query = query.join(AgendaItem.assembly)
            query = query.filter(Assembly.date == self.date)
        query = query.order_by(AgendaItem.number)
        return query

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> AgendaItem | None:
        return super().query().filter(AgendaItem.id == id).first()

    def by_number(self, number: int) -> AgendaItem | None:
        if not self.date:
            return None
        query = self.query().filter(AgendaItem.number == number)
        query = query.options(undefer(AgendaItem.content))
        return query.first()

    @cached_property
    def assembly(self) -> Assembly | None:
        if self.date is not None:
            query = self.session.query(Assembly)
            query = query.filter(Assembly.date == self.date)
            return query.first()
        return None

    def preloaded_by_assembly(self, assembly: Assembly) -> Query[AgendaItem]:
        query = self.session.query(AgendaItem)
        query = query.outerjoin(AgendaItem.vota)
        query = query.filter(AgendaItem.assembly_id == assembly.id)
        query = query.order_by(desc(AgendaItem.number))
        query = query.options(
            contains_eager(AgendaItem.vota),
            joinedload(AgendaItem.vota),
            joinedload(AgendaItem.files),
            joinedload(AgendaItem.vota, Votum.files),
            undefer(AgendaItem.content),
            defaultload(AgendaItem.vota).undefer(Votum.content)
        )
        return query
