from __future__ import annotations

from onegov.election_day.models import Ballot


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class BallotCollection:

    def __init__(self, session: Session):
        self.session = session

    def query(self) -> Query[Ballot]:
        return self.session.query(Ballot)

    def by_id(self, id: UUID) -> Ballot | None:
        return self.query().filter(Ballot.id == id).first()
