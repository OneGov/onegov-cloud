from __future__ import annotations

from onegov.core.collection import GenericCollection

from typing import TYPE_CHECKING

from onegov.parliament.models import Meeting

if TYPE_CHECKING:
    from uuid import UUID
    from sqlalchemy.orm import Query


class MeetingCollection(GenericCollection[Meeting]):

    @property
    def model_class(self) -> type[Meeting]:
        return Meeting

    def query(self) -> Query[Meeting]:
        query = super().query()
        return query.order_by(self.model_class.start_datetime.desc())

    def by_id(self, id: UUID | int | str) -> Meeting | None:
        return self.query().filter(Meeting.id == id).first()
