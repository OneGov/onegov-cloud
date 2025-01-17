from __future__ import annotations

from onegov.election_day.models import List


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class ListCollection:

    def __init__(self, session: Session):
        self.session = session

    def query(self) -> Query[List]:
        return self.session.query(List)

    def by_id(self, id: UUID) -> List | None:
        return self.query().filter(List.id == id).first()
