from datetime import date
from onegov.ballot import Vote, VoteCollection


def test_by_date(session):
    session.add(Vote(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="last",
        domain='canton',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="ignore",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = VoteCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.by_date(date(2015, 6, 14))] == [
        'first',
        'second',
        'last'
    ]


def test_get_latest(session):
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = VoteCollection(session)

    # sort by domain, then by date
    assert [v.title for v in collection.get_latest()] == ['latest']
