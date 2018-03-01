from datetime import date
from onegov.ballot import Ballot
from onegov.ballot import BallotCollection
from onegov.ballot import Vote


def test_ballots(session):
    vote = Vote(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.ballots.append(Ballot(type='proposal'))

    session.add(vote)
    session.flush()

    collection = BallotCollection(session)

    assert collection.query().count() == 1
    assert collection.by_id(vote.ballots[0].id) == vote.ballots[0]
