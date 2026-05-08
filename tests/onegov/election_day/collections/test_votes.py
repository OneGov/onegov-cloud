from __future__ import annotations

from datetime import date
from onegov.election_day.collections import VoteCollection
from onegov.election_day.models import Vote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_votes_by_date(session: Session) -> None:
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


def test_votes_by_id(session: Session) -> None:
    session.add(Vote(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    collection = VoteCollection(session)

    assert collection.by_id('first').title == "first"  # type: ignore[union-attr]
    assert collection.by_id('second').title == "second"  # type: ignore[union-attr]


def test_votes_get_latest(session: Session) -> None:
    collection = VoteCollection(session)
    assert collection.get_latest() is None

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

    # sort by domain, then by date
    assert [v.title for v in collection.get_latest()] == ['latest']  # type: ignore[union-attr]


def test_votes_get_years(session: Session) -> None:
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='federation',
        date=date(2015, 3, 14)
    ))
    session.add(Vote(
        title="even-older",
        domain='canton',
        date=date(2013, 6, 12)
    ))

    session.flush()

    assert VoteCollection(session).get_years() == [2015, 2013]


def test_votes_by_years(session: Session) -> None:
    session.add(Vote(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="older",
        domain='canton',
        date=date(2014, 6, 12)
    ))

    session.flush()

    votes = VoteCollection(session, year=2015)
    assert len(votes.by_year()) == 1
    assert votes.by_year()[0].title == "latest"

    assert len(votes.by_year(2014)) == 1
    assert votes.by_year(2014)[0].title == "older"

    assert len(votes.by_year(2013)) == 0


def test_votes_for_years(session: Session) -> None:
    votes = VoteCollection(session, year=2015)
    assert votes.for_year(2016).year == 2016


def test_votes_shortcode_order(session: Session) -> None:
    session.add(Vote(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(Vote(
        title="Z",
        shortcode="A",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    votes = VoteCollection(session, year=2015).by_year()
    assert votes[0].title == "Z"
    assert votes[1].title == "A"


def test_votes_pagination(session: Session) -> None:
    votes = VoteCollection(session)

    assert votes.page_index == 0
    assert votes.pages_count == 0
    assert votes.batch == ()

    for year in range(2008, 2011):
        for month in range(1, 13):
            session.add(Vote(
                title="Vote",
                domain='federation',
                date=date(year, month, 1)
            ))
            session.flush()

    assert votes.query().count() == 3 * 12

    votes = VoteCollection(session)
    assert votes.subset_count == 3 * 12

    votes = VoteCollection(session, year=2007)
    assert votes.subset_count == 0

    votes = VoteCollection(session, year=2008)
    assert votes.subset_count == 12
    assert all(e.date.year == 2008 for e in votes.batch)
    assert all(e.date.month > 2 for e in votes.batch)
    assert votes.next is not None
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all(e.date.year == 2008 for e in votes.next.batch)
    assert all(e.date.month < 3 for e in votes.next.batch)

    votes = VoteCollection(session, year=2009)
    assert votes.subset_count == 12
    assert all(e.date.year == 2009 for e in votes.batch)
    assert all(e.date.month > 2 for e in votes.batch)
    assert votes.next is not None
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all(e.date.year == 2009 for e in votes.next.batch)
    assert all(e.date.month < 3 for e in votes.next.batch)

    votes = VoteCollection(session, year=2010)
    assert votes.subset_count == 12
    assert all(e.date.year == 2010 for e in votes.batch)
    assert all(e.date.month > 2 for e in votes.batch)
    assert votes.next is not None
    assert len(votes.next.batch) == 12 - votes.batch_size
    assert all(e.date.year == 2010 for e in votes.next.batch)
    assert all(e.date.month < 3 for e in votes.next.batch)
