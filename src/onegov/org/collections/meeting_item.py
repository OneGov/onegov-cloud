from __future__ import annotations

from onegov.core.collection import GenericCollection

from typing import TYPE_CHECKING

from onegov.org.models.meeting_item import MeetingItem

if TYPE_CHECKING:
    from uuid import UUID
    from sqlalchemy.orm import Query


class MeetingItemCollection(GenericCollection[MeetingItem]):

    @property
    def model_class(self) -> type[MeetingItem]:
        return MeetingItem

    def query(self) -> Query[MeetingItem]:
        query = super().query()
        return query.order_by(self.model_class.number)

    def by_id(self, id: UUID | int | str) -> MeetingItem | None:
        return self.query().filter(MeetingItem.id == id).first()
