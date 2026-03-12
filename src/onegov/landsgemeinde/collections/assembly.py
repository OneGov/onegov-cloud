from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.landsgemeinde.models import Assembly
from sqlalchemy import desc
from sqlalchemy.orm import undefer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query
    from uuid import UUID


class AssemblyCollection(GenericCollection[Assembly]):

    @property
    def model_class(self) -> type[Assembly]:
        return Assembly

    def query(self) -> Query[Assembly]:
        return super().query().order_by(desc(Assembly.date))

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> Assembly | None:
        return self.query().filter(Assembly.id == id).first()

    def by_date(self, date_: date) -> Assembly | None:
        query = self.query().filter(Assembly.date == date_)
        query = query.options(undefer(Assembly.content))
        return query.first()
