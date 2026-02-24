from __future__ import annotations

from functools import cached_property
from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from sqlalchemy.orm import undefer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from uuid import UUID


class VotumCollection(GenericCollection[Votum]):

    def __init__(
        self,
        session: Session,
        date: date | None = None,
        agenda_item_number: int | None = None
    ) -> None:
        self.session = session
        self.date = date
        self.agenda_item_number = agenda_item_number

    @property
    def model_class(self) -> type[Votum]:
        return Votum

    def query(self) -> Query[Votum]:
        query = super().query()
        if self.date or self.agenda_item_number:
            query = query.join(Votum.agenda_item)
        if self.date:
            query = query.join(AgendaItem.assembly)
            query = query.filter(Assembly.date == self.date)
        if self.agenda_item_number:
            query = query.filter(AgendaItem.number == self.agenda_item_number)
        query = query.order_by(Votum.number)
        return query

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> Votum | None:
        return super().query().filter(Votum.id == id).first()

    def by_number(self, number: int) -> Votum | None:
        if not self.date or not self.agenda_item_number:
            return None
        query = self.query().filter(Votum.number == number)
        query = query.options(undefer(Votum.content))
        return query.first()

    @cached_property
    def assembly(self) -> Assembly | None:
        if self.date is not None:
            query = self.session.query(Assembly)
            query = query.filter(Assembly.date == self.date)
            return query.first()
        return None

    @cached_property
    def agenda_item(self) -> AgendaItem | None:
        if self.assembly is not None and self.agenda_item_number is not None:
            query = self.session.query(AgendaItem)
            query = query.filter(AgendaItem.assembly_id == self.assembly.id)
            query = query.filter(AgendaItem.number == self.agenda_item_number)
            return query.first()
        return None
