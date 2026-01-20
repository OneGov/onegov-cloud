from __future__ import annotations

from datetime import date
from onegov.election_day.collections import ElectionCompoundCollection
from onegov.election_day.models import ElectionCompound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_elections_by_date(session: Session) -> None:
    session.add(ElectionCompound(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="last",
        domain='canton',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="ignore",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    collection = ElectionCompoundCollection(session)

    # sort by title
    assert [v.title for v in collection.by_date(date(2015, 6, 14))] == [
        'first',
        'last',
        'second',
    ]


def test_elections_by_id(session: Session) -> None:
    session.add(ElectionCompound(
        title="first",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="second",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    collection = ElectionCompoundCollection(session)

    assert collection.by_id('first').title == "first"  # type: ignore[union-attr]
    assert collection.by_id('second').title == "second"  # type: ignore[union-attr]


def test_elections_get_latest(session: Session) -> None:
    collection = ElectionCompoundCollection(session)

    assert collection.get_latest() is None

    session.add(ElectionCompound(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="older",
        domain='canton',
        date=date(2015, 6, 12)
    ))

    session.flush()

    # sort by domain, then by date
    assert [v.title for v in collection.get_latest()] == ['latest']  # type: ignore[union-attr]


def test_elections_get_years(session: Session) -> None:
    session.add(ElectionCompound(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="older",
        domain='federation',
        date=date(2015, 3, 14)
    ))
    session.add(ElectionCompound(
        title="even-older",
        domain='canton',
        date=date(2013, 6, 12)
    ))

    session.flush()

    assert ElectionCompoundCollection(session).get_years() == [2015, 2013]


def test_elections_by_years(session: Session) -> None:
    session.add(ElectionCompound(
        title="latest",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="older",
        domain='canton',
        date=date(2014, 6, 12)
    ))

    session.flush()

    elections = ElectionCompoundCollection(session, year=2015)
    assert len(elections.by_year()) == 1
    assert elections.by_year()[0].title == "latest"

    assert len(elections.by_year(2014)) == 1
    assert elections.by_year(2014)[0].title == "older"

    assert len(elections.by_year(2013)) == 0


def test_elections_for_years(session: Session) -> None:
    elections = ElectionCompoundCollection(session, year=2015)
    assert elections.for_year(2016).year == 2016


def test_elections_shortcode_order(session: Session) -> None:
    session.add(ElectionCompound(
        title="A",
        shortcode="Z",
        domain='federation',
        date=date(2015, 6, 14)
    ))
    session.add(ElectionCompound(
        title="Z",
        shortcode="A",
        domain='federation',
        date=date(2015, 6, 14)
    ))

    session.flush()

    elections = ElectionCompoundCollection(session, year=2015).by_year()
    assert elections[0].title == "Z"
    assert elections[1].title == "A"


def test_elections_pagination(session: Session) -> None:
    elections = ElectionCompoundCollection(session)

    assert elections.page_index == 0
    assert elections.pages_count == 0
    assert elections.batch == ()

    for year in range(2008, 2011):
        for month in range(1, 13):
            session.add(ElectionCompound(
                title="ElectionCompound",
                domain='federation',
                date=date(year, month, 1)
            ))
            session.flush()

    assert elections.query().count() == 3 * 12

    elections = ElectionCompoundCollection(session)
    assert elections.subset_count == 3 * 12

    elections = ElectionCompoundCollection(session, year=2007)
    assert elections.subset_count == 0

    elections = ElectionCompoundCollection(session, year=2008)
    assert elections.subset_count == 12
    assert all(e.date.year == 2008 for e in elections.batch)
    assert all(e.date.month > 2 for e in elections.batch)
    assert elections.next is not None
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all(e.date.year == 2008 for e in elections.next.batch)
    assert all(e.date.month < 3 for e in elections.next.batch)

    elections = ElectionCompoundCollection(session, year=2009)
    assert elections.subset_count == 12
    assert all(e.date.year == 2009 for e in elections.batch)
    assert all(e.date.month > 2 for e in elections.batch)
    assert elections.next is not None
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all(e.date.year == 2009 for e in elections.next.batch)
    assert all(e.date.month < 3 for e in elections.next.batch)

    elections = ElectionCompoundCollection(session, year=2010)
    assert elections.subset_count == 12
    assert all(e.date.year == 2010 for e in elections.batch)
    assert all(e.date.month > 2 for e in elections.batch)
    assert elections.next is not None
    assert len(elections.next.batch) == 12 - elections.batch_size
    assert all(e.date.year == 2010 for e in elections.next.batch)
    assert all(e.date.month < 3 for e in elections.next.batch)


def test_elections_pagination_negative_page_index(session: Session) -> None:
    elections = ElectionCompoundCollection(session, page=-1)
    assert elections.page == 0
    assert elections.page_index == 0
    assert elections.page_by_index(-2).page == 0
    assert elections.page_by_index(-3).page_index == 0
