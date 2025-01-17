from __future__ import annotations

from onegov.election_day.models import Candidate


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


class CandidateCollection:

    def __init__(self, session: Session):
        self.session = session

    def query(self) -> Query[Candidate]:
        return self.session.query(Candidate)

    def by_id(self, id: UUID) -> Candidate | None:
        return self.query().filter(Candidate.id == id).first()
