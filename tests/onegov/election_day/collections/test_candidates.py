from __future__ import annotations

from datetime import date
from onegov.election_day.collections import CandidateCollection
from onegov.election_day.models import Candidate
from onegov.election_day.models import Election


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_candidates(session: Session) -> None:
    election = Election(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14)
    )
    election.candidates.append(
        Candidate(
            candidate_id='1',
            first_name='Hans',
            family_name='Müller',
            elected=False
        )
    )
    session.add(election)
    session.flush()

    collection = CandidateCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(
        election.candidates[0].id) == election.candidates[0]
