from __future__ import annotations

from datetime import date
from onegov.election_day.collections import BallotCollection
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_ballots(session: Session) -> None:
    vote = Vote(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    )
    assert vote.proposal  # create
    session.add(vote)
    session.flush()

    collection = BallotCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(vote.ballots[0].id) == vote.ballots[0]
