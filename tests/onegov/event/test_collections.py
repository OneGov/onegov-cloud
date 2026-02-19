from __future__ import annotations

import pytest
import transaction

from datetime import date
from datetime import datetime
from datetime import timedelta
from freezegun import freeze_time
from markupsafe import escape
from onegov.event import Event
from onegov.event import EventCollection
from onegov.event.collections.events import EventImportItem
from onegov.event import Occurrence
from onegov.event import OccurrenceCollection
from onegov.form import parse_formcode, flatten_fieldsets
from onegov.gis import Coordinates
from sedate import replace_timezone
from sedate import standardize_date


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Query, Session

# keep dates in the future
next_year = datetime.today().year + 1


class DummyRequest:

    def link(self, item: object) -> str:
        return 'https://example.org/{}/{}'.format(
            item.__class__.__name__.lower(),
            getattr(item, 'name' or '?')
        )


def tzdatetime(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    timezone: str
) -> datetime:
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_event_collection(session: Session) -> None:
    events = EventCollection(session)
    assert events.query().count() == 0

    event_1 = events.add(
        title='Squirrel Park Visit',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
        timezone='US/Eastern',
        content={
            'description': '<em>Furry</em> things will happen!'
        },
        location='Squirrel Park',
        tags=['fun', 'animals'],
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
            'UNTIL=20150616T220000Z'
        )
    )
    event_1.submit()
    event_1.publish()
    event_2 = events.add(
        title='History of the Squirrel Park',
        start=datetime(2015, 6, 18, 14, 00),
        end=datetime(2015, 6, 18, 16, 00),
        timezone='US/Eastern',
        content={
            'description': 'Learn how the Park got so <em>furry</em>!'
        },
        location='Squirrel Park',
        tags=['history']
    )
    event_2.submit()
    event_2.publish()
    assert events.query().count() == 2

    assert events.by_id(event_1.id) == event_1
    assert events.by_id(event_2.id) == event_2

    events.delete(event_1)
    events.delete(event_2)
    assert events.query().count() == 0
    assert session.query(Occurrence).count() == 0


def test_event_collection_remove_stale_events(session: Session) -> None:
    timezone = 'UTC'

    events = EventCollection(session)
    events.add(
        title='Event', timezone=timezone,
        start=datetime(2010, 6, 1, 10),
        end=datetime(2010, 6, 1, 10) + timedelta(hours=1),
    )
    assert events.query().count() == 1

    max_stale = standardize_date(datetime.today() + timedelta(days=2), 'UTC')
    events.remove_stale_events(max_stale=max_stale)
    assert events.query().count() == 0


def test_event_collection_pagination(session: Session) -> None:
    events = EventCollection(session)

    assert events.page_index == 0
    assert events.pages_count == 0
    assert events.batch == ()

    for year in range(2008, 2011):
        for month in range(1, 13):
            event = events.add(
                title='Event {0}-{1}'.format(year, month),
                start=datetime(year, month, 18, 14, 00),
                end=datetime(year, month, 18, 16, 00),
                timezone='US/Eastern',
                tags=['month-{0}'.format(month)],
                recurrence=(
                    f'RRULE:FREQ=WEEKLY;'
                    f'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                    f'UNTIL={year}{month:02}18T220000Z'
                )
            )
            event.submit()
            if year > 2008:
                event.publish()
            if year > 2009:
                event.withdraw()
    assert events.query().count() == 3 * 12

    events = EventCollection(session, state='initiated')
    assert events.subset_count == 0

    events = events.for_state('submitted')
    assert events.subset_count == 12
    assert all(e.start.year == 2008 for e in events.batch)
    assert all(e.start.month < 11 for e in events.batch)
    assert events.next is not None
    assert len(events.next.batch) == 12 - events.batch_size
    assert all(e.start.year == 2008 for e in events.next.batch)
    assert all(e.start.month > 10 for e in events.next.batch)
    assert events.page_by_index(1) == events.next

    events = events.for_state('published')
    assert events.subset_count == 12
    assert all(e.start.year == 2009 for e in events.batch)
    assert all(e.start.month < 11 for e in events.batch)
    assert events.next is not None
    assert len(events.next.batch) == 12 - events.batch_size
    assert all(e.start.year == 2009 for e in events.next.batch)
    assert all(e.start.month > 10 for e in events.next.batch)

    events = events.for_state('withdrawn')
    assert events.subset_count == 12
    assert all(e.start.year == 2010 for e in events.batch)
    assert all(e.start.month < 11 for e in events.batch)
    assert events.next is not None
    assert len(events.next.batch) == 12 - events.batch_size
    assert all(e.start.year == 2010 for e in events.next.batch)
    assert all(e.start.month > 10 for e in events.next.batch)


def test_event_pagination_negative_page_index(session: Session) -> None:
    events = EventCollection(session, page=-1)
    assert events.page == 0
    assert events.page_index == 0
    assert events.page_by_index(-2).page == 0
    assert events.page_by_index(-3).page_index == 0

    with pytest.raises(AssertionError):
        EventCollection(None, page=None)  # type: ignore[arg-type]


def test_occurrence_collection(session: Session) -> None:
    event = EventCollection(session).add(
        title='Squirrel Park Visit',
        start=datetime(next_year, 6, 16, 9, 30),
        end=datetime(next_year, 6, 16, 18, 00),
        timezone='Pacific/Auckland',
        location='Squirrel Park',
        tags=['fun', 'park', 'animals'],
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
            'UNTIL=20150619T220000Z'
        )
    )
    event.submit()
    event.publish()
    event = EventCollection(session).add(
        title='History of the Squirrel Park',
        start=datetime(next_year, 6, 18, 14, 00),
        end=datetime(next_year, 6, 18, 16, 00),
        timezone='Europe/Zurich',
        location='Squirrel Park',
        tags=['history', 'park', 'fun']
    )
    event.submit()
    event.publish()
    event = EventCollection(session).add(
        title='Zirkus Knie - Manage frei!',
        start=datetime(next_year, 6, 20, 19, 00),
        end=datetime(next_year, 6, 20, 21, 00),
        timezone='Europe/Zurich',
        location='Allmend Luzern',
        tags=['fun']
    )
    event.submit()
    event.publish()

    # add event in the past
    event = EventCollection(session).add(
        title='Wild West Tour',
        start=datetime(2023, 7, 12, 00, 00),
        end=datetime(2023, 7, 12, 22, 00),
        timezone='US/Central',
        location='USA',
        tags=['cowboy']
    )
    event.submit()
    event.publish()

    occurrences = OccurrenceCollection(session)
    assert sorted(occurrences.used_timezones) == ['Europe/Zurich',
                                                  'Pacific/Auckland',
                                                  'US/Central']

    # tags counts only from future events
    assert dict(sorted(occurrences.tag_counts.items())) == {'animals': 1,
                                                            'fun': 3,
                                                            'history': 1,
                                                            'park': 2}
    assert occurrences.tag_counts['not_existing_tag'] == 0

    # tags only from future events
    assert sorted(occurrences.used_tags) == ['animals', 'fun', 'history',
                                             'park']

    assert OccurrenceCollection(session, range='today').start == date.today()
    assert OccurrenceCollection(session, range='today').end == date.today()


def test_occurrence_collection_query(session: Session) -> None:
    event = EventCollection(session).add(
        title='Squirrel Park Visit',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
        timezone='Europe/Zurich',
        location='Squirrel Park',
        tags=['fun', 'park', 'animals'],
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
            'UNTIL=20150619T220000Z'
        )
    )
    event.submit()
    event.publish()
    event = EventCollection(session).add(
        title='History of the Squirrel Park',
        start=datetime(2015, 6, 18, 14, 00),
        end=datetime(2015, 6, 18, 16, 00),
        timezone='Europe/Zurich',
        location='Squirrel Park Visitor Center',
        tags=['history']
    )
    event.submit()
    event.publish()

    def query(**kwargs: Any) -> Query[Occurrence]:
        return OccurrenceCollection(session, **kwargs).query()

    assert query().count() == 0
    assert query(outdated=True).count() == 5

    assert query(outdated=True, tags=['animals']).count() == 4
    assert query(outdated=True, tags=['park']).count() == 4
    assert query(outdated=True, tags=['park', 'fun']).count() == 4
    assert query(outdated=True, tags=['history']).count() == 1
    assert query(outdated=True, tags=['history', 'fun']).count() == 5
    assert query(outdated=True, tags=[]).count() == 5

    assert query(outdated=True, locations=['Squirrel']).count() == 5
    assert query(outdated=True, locations=['Squirrel Park']).count() == 5
    assert query(outdated=True, locations=['Squirrel', 'Park']).count() == 5
    # test random user input
    assert query(
        outdated=True, locations=['Squirrel Park\'\',,"").")']).count() == 5
    assert query(outdated=True, locations=['Center']).count() == 1
    assert query(outdated=True, locations=['squirrel', 'park']).count() == 0
    assert query(outdated=True, locations=[]).count() == 5

    assert query(outdated=True, start=date(2015, 6, 17)).count() == 4
    assert query(outdated=True, start=date(2015, 6, 18)).count() == 3
    assert query(outdated=True, start=date(2015, 6, 19)).count() == 1

    assert query(outdated=True, end=date(2015, 6, 19)).count() == 5
    assert query(outdated=True, end=date(2015, 6, 18)).count() == 4
    assert query(outdated=True, end=date(2015, 6, 17)).count() == 2

    assert query(
        outdated=True, start=date(2015, 6, 17), end=date(2015, 6, 18)
    ).count() == 3
    assert query(
        outdated=True, start=date(2015, 6, 18), end=date(2015, 6, 18)
    ).count() == 2
    assert query(
        outdated=True, start=date(2015, 6, 18), end=date(2015, 6, 18),
        tags=['history']
    ).count() == 1

    with freeze_time("2015-06-17"):
        assert query(outdated=True, range='today').count() == 1
        assert query(outdated=True, range='tomorrow').count() == 2
        assert query(outdated=True, range='weekend').count() == 1
        assert query(outdated=True, range='week').count() == 5
        assert query(outdated=True, range='month').count() == 5
        assert query(outdated=True, range='past').count() == 1

        assert query(outdated=False, range='today').count() == 1
        assert query(outdated=False, range='tomorrow').count() == 2
        assert query(outdated=False, range='weekend').count() == 1
        assert query(outdated=False, range='week').count() == 4
        assert query(outdated=False, range='month').count() == 4
        assert query(outdated=False, range='past').count() == 1


def test_occurrence_collection_pagination(session: Session) -> None:
    occurrences = OccurrenceCollection(session)
    assert occurrences.page_index == 0
    assert occurrences.pages_count == 0
    assert occurrences.batch == ()

    for year in range(2008, 2011):
        for month in range(1, 13):
            event = EventCollection(session).add(
                title='Event {0}-{1}'.format(year, month),
                start=datetime(year, month, 18, 14, 00),
                end=datetime(year, month, 18, 16, 00),
                timezone='US/Eastern',
                tags=['month-{0}'.format(month)],
                recurrence=(
                    f'RRULE:FREQ=WEEKLY;'
                    f'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                    f'UNTIL={year}{month:02}21T220000Z'
                )
            )
            event.submit()
            if year > 2008:
                event.publish()
            if year > 2009:
                event.withdraw()

    occurrences = OccurrenceCollection(
        session,
        outdated=True
    )
    assert occurrences.query().count() == 4 * 12

    occurrences = OccurrenceCollection(
        session,
        outdated=True
    )
    assert occurrences.subset_count == 48
    assert all([o.start.year == 2009 for o in occurrences.batch])
    assert occurrences.page_by_index(1) == occurrences.next

    occurrences = OccurrenceCollection(
        session,
        outdated=True,
        start=date(2009, 12, 1)
    )
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 12
                for o in occurrences.batch])

    occurrences = OccurrenceCollection(
        session,
        end=date(2009, 1, 31),
        outdated=True
    )
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 1
                for o in occurrences.batch])

    occurrences = OccurrenceCollection(
        session,
        start=date(2009, 5, 1),
        end=date(2009, 6, 30),
        outdated=True
    )
    assert occurrences.subset_count == 8
    assert all([o.start.year == 2009 and o.start.month in [5, 6]
                for o in occurrences.batch])

    occurrences = OccurrenceCollection(
        session,
        outdated=True,
        tags=['month-7', 'month-8']
    )
    assert occurrences.subset_count == 8
    assert all([o.start.year == 2009 and o.start.month in [7, 8]
                for o in occurrences.batch])

    occurrences = OccurrenceCollection(
        session,
        start=date(2009, 5, 1),
        end=date(2009, 6, 30),
        outdated=True,
        tags=['month-6']
    )
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 6
                for o in occurrences.batch])


def test_occurrence_collection_for_toggled_keyword_value(
    session: Session
) -> None:

    config = {'keywords': ['Filter'], 'order': []}
    definition = """Filter *=
    ( ) Filter A
    ( ) Filter B
    ( ) Filter C
    """

    fields = tuple(flatten_fieldsets(parse_formcode(definition)))
    occurrences = OccurrenceCollection(
        session=session,
        filter_keywords={'filter': ['Filter A']}
    )
    occurrences.set_event_filter_configuration(config)
    occurrences.set_event_filter_fields(fields)

    occurrences = occurrences.for_toggled_keyword_value(
        'filter',
        'Filter B',
        singular=True
    )
    assert occurrences.filter_keywords == {'filter': ['Filter B']}

    occurrences = occurrences.for_toggled_keyword_value(
        'filter',
        'Filter B',
        singular=True
    )
    assert occurrences.filter_keywords == {}

    occurrences = occurrences.for_toggled_keyword_value(
        'filter',
        'Filter C',
        singular=True
    )
    assert occurrences.filter_keywords == {'filter': ['Filter C']}

    occurrences = occurrences.for_toggled_keyword_value(
        'filter',
        'Filter X',
        singular=False
    )
    assert occurrences.filter_keywords == {'filter': ['Filter C', 'Filter X']}
    occurrences = occurrences.for_toggled_keyword_value(
        'filter',
        'Filter X',
        singular=False
    )
    assert occurrences.filter_keywords == {'filter': ['Filter C']}


def test_occurrence_collection_for_filter(session: Session) -> None:
    occurrences = OccurrenceCollection(session=session)
    occurrences = occurrences.for_filter()
    assert occurrences.range is None
    assert occurrences.start is None
    assert occurrences.end is None
    assert occurrences.outdated is False
    assert occurrences.tags == []
    assert occurrences.locations == []
    assert occurrences.filter_keywords == {}

    occurrences = OccurrenceCollection(
        session=session,
        start=date(2009, 5, 1),
        end=date(2009, 6, 30),
        tags=['month-6'],
        locations=['Bar'],
        filter_keywords={'filter': ['Filter A']}
    )
    occurrences = occurrences.for_filter()
    assert occurrences.range is None
    assert occurrences.start == date(2009, 5, 1)
    assert occurrences.end == date(2009, 6, 30)
    assert occurrences.outdated is False
    assert occurrences.tags == ['month-6']
    assert occurrences.locations == ['Bar']

    occurrences = occurrences.for_filter(start=date(2010, 5, 1))
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end == date(2009, 6, 30)
    assert occurrences.outdated is False
    assert occurrences.tags == ['month-6']
    assert occurrences.locations == ['Bar']

    occurrences = occurrences.for_filter(end=None, outdated=True)
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end is None
    assert occurrences.outdated is True
    assert occurrences.tags == ['month-6']
    assert occurrences.locations == ['Bar']

    occurrences = occurrences.for_filter(tags=[], locations=[])
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end is None
    assert occurrences.outdated is True
    assert occurrences.tags == []
    assert occurrences.locations == []

    occurrences = occurrences.for_filter(tags=['a', 'b'], locations=['A', 'B'])
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end is None
    assert occurrences.outdated is True
    assert occurrences.tags == ['a', 'b']
    assert occurrences.locations == ['A', 'B']

    occurrences = occurrences.for_filter(tag='c', location='C', range='today')
    assert occurrences.range == 'today'
    assert occurrences.start == date.today()
    assert occurrences.end == date.today()
    assert occurrences.outdated is True
    assert occurrences.tags == ['a', 'b', 'c']
    assert occurrences.locations == ['A', 'B', 'C']

    occurrences = occurrences.for_filter(tag='a', location='A')
    assert occurrences.range == 'today'
    assert occurrences.start == date.today()
    assert occurrences.end == date.today()
    assert occurrences.outdated is True
    assert occurrences.tags == ['b', 'c']
    assert occurrences.locations == ['B', 'C']

    occurrences = occurrences.for_filter(range='today', start=date(2010, 5, 1))
    assert occurrences.range == 'today'
    assert occurrences.start == date.today()
    assert occurrences.end == date.today()
    assert occurrences.outdated is True
    assert occurrences.tags == ['b', 'c']
    assert occurrences.locations == ['B', 'C']

    occurrences = occurrences.for_filter(start=date(2010, 5, 1))
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end == date.today()
    assert occurrences.outdated is True
    assert occurrences.tags == ['b', 'c']
    assert occurrences.locations == ['B', 'C']

    occurrences = occurrences.for_filter(range='-', end=date(2010, 5, 1))  # type: ignore[arg-type]
    assert occurrences.range is None
    assert occurrences.start == date(2010, 5, 1)
    assert occurrences.end == date(2010, 5, 1)
    assert occurrences.outdated is True
    assert occurrences.tags == ['b', 'c']
    assert occurrences.locations == ['B', 'C']


def test_occurrence_collection_outdated(session: Session) -> None:
    with freeze_time("2024-02-28"):
        today = date.today()
        for year in (today.year - 1, today.year, today.year + 1):
            event = EventCollection(session).add(
                title='Event {0}-{1}'.format(year, today.month),
                start=datetime(year, today.month, today.day, 0, 0),
                end=datetime(year, today.month, today.day, 23, 59),
                timezone='US/Eastern'
            )
            event.submit()
            event.publish()

        def query(**kwargs: Any) -> Query[Occurrence]:
            return OccurrenceCollection(session, **kwargs).query()

        assert query(outdated=False).count() == 2
        assert query(outdated=True).count() == 3

        assert query(start=date(today.year - 1, 1, 1),
                     outdated=False).count() == 2
        assert query(start=date(today.year - 1, 1, 1),
                     outdated=True).count() == 3

        assert query(end=date.today(), outdated=False).count() == 1
        assert query(end=date.today(), outdated=True).count() == 2


def test_occurrence_collection_range_to_dates() -> None:
    def to_dates(range: object) -> tuple[date | None, date | None]:
        return OccurrenceCollection(None).range_to_dates(range)  # type: ignore[arg-type]

    with freeze_time("2018-12-03"):
        assert to_dates('today') == (date(2018, 12, 3), date(2018, 12, 3))
        assert to_dates('tomorrow') == (date(2018, 12, 4), date(2018, 12, 4))
        assert to_dates('weekend') == (date(2018, 12, 7), date(2018, 12, 9))
        assert to_dates('week') == (date(2018, 12, 3), date(2018, 12, 9))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 2))
    with freeze_time("2018-12-06"):
        assert to_dates('today') == (date(2018, 12, 6), date(2018, 12, 6))
        assert to_dates('tomorrow') == (date(2018, 12, 7), date(2018, 12, 7))
        assert to_dates('weekend') == (date(2018, 12, 7), date(2018, 12, 9))
        assert to_dates('week') == (date(2018, 12, 3), date(2018, 12, 9))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 5))
    with freeze_time("2018-12-07"):
        assert to_dates('today') == (date(2018, 12, 7), date(2018, 12, 7))
        assert to_dates('tomorrow') == (date(2018, 12, 8), date(2018, 12, 8))
        assert to_dates('weekend') == (date(2018, 12, 7), date(2018, 12, 9))
        assert to_dates('week') == (date(2018, 12, 3), date(2018, 12, 9))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 6))
    with freeze_time("2018-12-08"):
        assert to_dates('today') == (date(2018, 12, 8), date(2018, 12, 8))
        assert to_dates('tomorrow') == (date(2018, 12, 9), date(2018, 12, 9))
        assert to_dates('weekend') == (date(2018, 12, 7), date(2018, 12, 9))
        assert to_dates('week') == (date(2018, 12, 3), date(2018, 12, 9))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 7))
    with freeze_time("2018-12-09"):
        assert to_dates('today') == (date(2018, 12, 9), date(2018, 12, 9))
        assert to_dates('tomorrow') == (date(2018, 12, 10), date(2018, 12, 10))
        assert to_dates('weekend') == (date(2018, 12, 7), date(2018, 12, 9))
        assert to_dates('week') == (date(2018, 12, 3), date(2018, 12, 9))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 8))
    with freeze_time("2018-12-10"):
        assert to_dates('today') == (date(2018, 12, 10), date(2018, 12, 10))
        assert to_dates('tomorrow') == (date(2018, 12, 11), date(2018, 12, 11))
        assert to_dates('weekend') == (date(2018, 12, 14), date(2018, 12, 16))
        assert to_dates('week') == (date(2018, 12, 10), date(2018, 12, 16))
        assert to_dates('month') == (date(2018, 12, 1), date(2018, 12, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2018, 12, 9))
    with freeze_time("2019-01-31"):
        assert to_dates('today') == (date(2019, 1, 31), date(2019, 1, 31))
        assert to_dates('tomorrow') == (date(2019, 2, 1), date(2019, 2, 1))
        assert to_dates('weekend') == (date(2019, 2, 1), date(2019, 2, 3))
        assert to_dates('week') == (date(2019, 1, 28), date(2019, 2, 3))
        assert to_dates('month') == (date(2019, 1, 1), date(2019, 1, 31))
        assert to_dates('past') == (date(2000, 1, 1), date(2019, 1, 30))

    assert to_dates(None) == (None, None)
    assert to_dates('') == (None, None)
    assert to_dates(1) == (None, None)
    assert to_dates('never') == (None, None)

    assert OccurrenceCollection(None).range_to_dates(  # type: ignore[arg-type]
        '', start=date(2019, 1, 1), end=date(2019, 1, 31)  # type: ignore[arg-type]
    ) == (date(2019, 1, 1), date(2019, 1, 31))


def test_occurrence_collection_used_tags_tag_count(session: Session) -> None:
    """ Two occurrences one today the second some when in the future."""
    year = date.today().year
    month = date.today().month
    day = date.today().day
    next = date.today() + timedelta(days=3)

    event = EventCollection(session).add(
        title='Dampferträffe',
        start=datetime(year, month, day, 9, 30),
        end=datetime(year, month, day, 16, 30),
        timezone='Europe/Zurich',
        content={
            'description': 'Liebe Dampferfreunde!'
        },
        location='Luzern am Quai',
        tags=['dampfer', 'treffen'],
        recurrence=f'RDATE:{next.strftime("%Y%m%d")}T000000Z',
    )
    event.submit()
    event.publish()
    session.flush()

    occurrences = OccurrenceCollection(session, outdated=True)

    assert dict(sorted(occurrences.tag_counts.items())) == {'dampfer': 2,
                                                            'treffen': 2}
    assert sorted(occurrences.used_tags) == ['dampfer', 'treffen']


def test_unique_names(session: Session) -> None:
    events = EventCollection(session)
    added = [
        events.add(
            title='Squirrel Park Visit',
            start=datetime(2015, 6, 16, 9, 30),
            end=datetime(2015, 6, 16, 18, 00),
            timezone='US/Eastern'
        ) for x in range(11)
    ]
    assert added[0].name == 'squirrel-park-visit'
    assert added[1].name == 'squirrel-park-visit-1'
    assert added[2].name == 'squirrel-park-visit-2'
    assert added[3].name == 'squirrel-park-visit-3'
    assert added[4].name == 'squirrel-park-visit-4'
    assert added[5].name == 'squirrel-park-visit-5'
    assert added[6].name == 'squirrel-park-visit-6'
    assert added[7].name == 'squirrel-park-visit-7'
    assert added[8].name == 'squirrel-park-visit-8'
    assert added[9].name == 'squirrel-park-visit-9'
    assert added[10].name == 'squirrel-park-visit-10'

    events.delete(added[6])
    event = events.add(
        title='Squirrel Park Visit',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
        timezone='US/Eastern',
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
            'UNTIL=20150620T220000Z'
        )
    )
    assert event.name == 'squirrel-park-visit-6'

    event.submit()
    event.publish()
    assert event.occurrences[0].name == 'squirrel-park-visit-6-2015-06-16'
    assert event.occurrences[1].name == 'squirrel-park-visit-6-2015-06-17'
    assert event.occurrences[2].name == 'squirrel-park-visit-6-2015-06-18'
    assert event.occurrences[3].name == 'squirrel-park-visit-6-2015-06-19'
    assert event.occurrences[4].name == 'squirrel-park-visit-6-2015-06-20'

    assert events.by_name('test') is None
    assert events.by_name('squirrel-park-visit-6') == event

    occurrences = OccurrenceCollection(session)
    assert occurrences.by_name('test') is None

    occurrence = occurrences.by_name('squirrel-park-visit-6-2015-06-20')
    assert occurrence == event.occurrences[4]


def test_unicode(session: Session) -> None:
    event = EventCollection(session).add(
        title='Salon du mieux-vivre, 16e édition',
        start=datetime(next_year, 6, 16, 9, 30),
        end=datetime(next_year, 6, 16, 18, 00),
        timezone='Europe/Zurich',
        content={
            'description': 'Rendez-vous automnal des médecines.'
        },
        location='Salon du mieux-vivre à Saignelégier',
        tags=['salons', 'congrès']
    )
    event.submit()
    event.publish()
    event = EventCollection(session).add(
        title='Témoins de Jéhovah',
        start=datetime(next_year, 6, 18, 14, 00),
        end=datetime(next_year, 6, 18, 16, 00),
        timezone='Europe/Zurich',
        content={
            'description': 'Congrès en français et espagnol.'
        },
        location='Salon du mieux-vivre à Saignelégier',
        tags=['témoins']
    )
    event.submit()
    event.publish()
    session.flush()

    occurrences = OccurrenceCollection(session, outdated=True)

    assert dict(sorted(occurrences.tag_counts.items())) == {'congrès': 1,
                                                            'salons': 1,
                                                            'témoins': 1}
    assert sorted(occurrences.used_tags) == ['congrès', 'salons', 'témoins']

    assert occurrences.query().count() == 2

    occurrences = occurrences.for_filter(tags=['congrès'])
    occurrence = occurrences.query().one()
    assert occurrence.title == 'Salon du mieux-vivre, 16e édition'
    assert occurrence.location == 'Salon du mieux-vivre à Saignelégier'
    assert sorted(occurrence.tags) == ['congrès', 'salons']
    assert occurrence.event.description \
           == 'Rendez-vous automnal des médecines.'

    occurrences = occurrences.for_filter(tags=['témoins'])
    occurrence = occurrences.query().one()
    assert occurrence.title == 'Témoins de Jéhovah'
    assert occurrence.location == 'Salon du mieux-vivre à Saignelégier'
    assert occurrence.tags == ['témoins']
    assert occurrence.event.description == 'Congrès en français et espagnol.'


def test_as_ical(session: Session) -> None:
    def as_ical(occurrences: OccurrenceCollection) -> list[str]:
        result = occurrences.as_ical(DummyRequest())  # type: ignore[arg-type]
        return result.decode().strip().splitlines()

    occurrences = OccurrenceCollection(session)
    assert sorted(as_ical(occurrences)) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'END:VCALENDAR',
    ])

    events = EventCollection(session)
    with freeze_time("2014-01-01"):
        event = events.add(
            title='Squirrel Park Visit',
            start=datetime(2015, 6, 16, 9, 30),
            end=datetime(2015, 6, 16, 18, 00),
            timezone='US/Eastern',
            content={
                'description': '<em>Furry</em> things will happen!'
            },
            location='Squirrel Park',
            tags=['fun', 'animals'],
            recurrence=(
                'RRULE:FREQ=WEEKLY;'
                'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
                'UNTIL=20150616T220000Z'
            ),
            coordinates=Coordinates(47.051752750515746, 8.305739625357093)
        )
        event.submit()
        event.publish()

        event = events.add(
            title='History of the Squirrel Park',
            start=datetime(2015, 6, 18, 14, 00),
            end=datetime(2015, 6, 18, 16, 00),
            timezone='US/Eastern',
            content={
                'description': 'Learn how the Park got so <em>furry</em>!'
            },
            location='Squirrel Park',
            tags=['history'],
            coordinates=Coordinates(47.051752750515746, 8.305739625357093)
        )
        event.submit()
        event.publish()

        session.flush()

    occurrences = OccurrenceCollection(session)
    assert sorted(as_ical(occurrences)) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'END:VCALENDAR',
    ])

    occurrences = occurrences.for_filter(start=date(2015, 6, 1))
    assert sorted(as_ical(occurrences)) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'END:VCALENDAR',
    ])

    occurrences = occurrences.for_filter(outdated=True)
    assert sorted(as_ical(occurrences)) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Visit',
        'UID:squirrel-park-visit-2015-06-16@onegov.event',
        'DTSTART:20150616T133000Z',
        'DTEND:20150616T220000Z',
        'DTSTAMP:20140101T000000Z',
        'RRULE:FREQ=WEEKLY;UNTIL=20150616T220000Z;BYDAY=MO,TU,WE,TH,FR,SA,SU',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'BEGIN:VEVENT',
        'UID:history-of-the-squirrel-park-2015-06-18@onegov.event',
        'SUMMARY:History of the Squirrel Park',
        'DTSTART:20150618T180000Z',
        'DTEND:20150618T200000Z',
        'DTSTAMP:20140101T000000Z',
        'DESCRIPTION:Learn how the Park got so <em>furry</em>!',
        'CATEGORIES:history',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/history-of-the-squirrel-park',
        'END:VEVENT',
        'END:VCALENDAR'
    ])

    occurrences = occurrences.for_filter(
        start=date(2015, 6, 18),
        end=date(2018, 6, 18),
        tags=['history']
    )
    assert sorted(as_ical(occurrences)) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'UID:history-of-the-squirrel-park-2015-06-18@onegov.event',
        'SUMMARY:History of the Squirrel Park',
        'DTSTART:20150618T180000Z',
        'DTEND:20150618T200000Z',
        'DTSTAMP:20140101T000000Z',
        'DESCRIPTION:Learn how the Park got so <em>furry</em>!',
        'CATEGORIES:history',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/history-of-the-squirrel-park',
        'END:VEVENT',
        'END:VCALENDAR'
    ])


def test_from_import(session: Session) -> None:
    events = EventCollection(session)

    added, updated, purged = events.from_import([
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title A',
                location='Location A',
                tags=['Tag A.1', 'Tag A.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description A',
                organizer='Organizer A',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-1-A'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        ),
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title B',
                location='Location B',
                tags=['Tag B.1', 'Tag B.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description B',
                organizer='Organizer B',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-1-B'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )
    ])
    assert (len(added), len(updated), len(purged)) == (2, 0, 0)

    def items() -> Iterator[EventImportItem]:
        yield EventImportItem(
            event=Event(
                state='initiated',
                title='Title C',
                location='Location C',
                tags=['Tag C.1', 'Tag C.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description C',
                organizer='Organizer C',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-2-C'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )

    added, updated, purged = events.from_import(items())
    assert (len(added), len(updated), len(purged)) == (1, 0, 0)

    # Already imported
    assert events.from_import([
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title C',
                location='Location C',
                tags=['Tag C.1', 'Tag C.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description C',
                organizer='Organizer C',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-2-C'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )
    ]) == ([], [], [])

    # Update and purge
    a, u, p = events.from_import([
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title',
                location='Location A',
                tags=['Tag A.1', 'Tag A.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description A',
                organizer='Organizer A',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-1-A'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )
    ], ['import-1'])
    assert (len(a), len(u), len(p)) == (0, 1, 1)
    assert events.subset_count == 2

    # Don't purge
    assert events.from_import(['import-1-A'], ['import-1']) == ([], [], [])
    assert events.subset_count == 2

    # Withdraw
    events.by_name('title-c').withdraw()  # type: ignore[union-attr]
    assert events.from_import([
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title C',
                location='Location C',
                tags=['Tag C.1', 'Tag C.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description C',
                organizer='Organizer C',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-2-C'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )
    ]) == ([], [], [])
    assert events.by_name('title-c').state == 'withdrawn'  # type: ignore[union-attr]

    # future only events option
    a, u, p = events.from_import([
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title D past',
                location='Location D past',
                tags=['Tag D.1', 'Tag D.2'],
                start=tzdatetime(2020, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(2020, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description D past',
                organizer='Organizer D past',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    'UNTIL=20200616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-2-D'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        ),
        EventImportItem(
            event=Event(
                state='initiated',
                title='Title D future',
                location='Location D future',
                tags=['Tag D.1', 'Tag D.2'],
                start=tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern'),
                end=tzdatetime(next_year, 6, 16, 18, 00, 'US/Eastern'),
                timezone='US/Eastern',
                description='Description D future',
                organizer='Organizer D future',
                recurrence=(
                    'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={next_year}0616T220000Z;'
                    'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
                coordinates=Coordinates(48.051752750515746, 9.305739625357093),
                source='import-2-D'
            ),
            image=None,
            image_filename=None,
            pdf=None,
            pdf_filename=None,
        )
    ], future_events_only=True)
    # only adding the future event
    assert (len(a), len(u), len(p)) == (1, 0, 0)


def test_from_ical(session: Session) -> None:
    events = EventCollection(session)

    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'END:VCALENDAR',
    ]))
    assert events.query().count() == 0

    # UTC-date
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Virsit',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART:{next_year}0616T133100Z',
        f'DTEND:{next_year}0616T220100Z',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0619T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Par',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.title == 'Squirrel Park Virsit'
    assert event.description == escape('<em>Furri</em> things will happen!')
    assert event.location == 'Squirrel Par'
    assert event.start == tzdatetime(next_year, 6, 16, 9, 31, 'US/Eastern')
    assert str(event.start.tzinfo) == 'UTC'
    assert event.end == tzdatetime(next_year, 6, 16, 18, 1, 'US/Eastern')
    assert str(event.end.tzinfo) == 'UTC'
    assert event.timezone == 'Europe/Zurich'
    assert event.recurrence == (
        'RRULE:FREQ=WEEKLY;'
        f'UNTIL={next_year}0619T220000Z;'
        'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    assert [o.start.day for o in event.occurrences] == [16, 17, 18, 19]
    assert sorted(event.tags) == ['animals', 'fun']
    assert event.coordinates.lat
    assert int(event.coordinates.lat) == 48
    assert event.coordinates.lon
    assert int(event.coordinates.lon) == 9

    # update
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Visit',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART:{next_year}0616T133000Z',
        f'DTEND:{next_year}0616T220000Z',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0620T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.title == 'Squirrel Park Visit'
    assert event.description == escape('<em>Furry</em> things will happen!')
    assert event.location == 'Squirrel Park'
    assert event.start == tzdatetime(next_year, 6, 16, 9, 30, 'US/Eastern')
    assert str(event.start.tzinfo) == 'UTC'
    assert event.end == tzdatetime(next_year, 6, 16, 18, 0, 'US/Eastern')
    assert str(event.end.tzinfo) == 'UTC'
    assert event.timezone == 'Europe/Zurich'
    assert event.recurrence == (
        'RRULE:FREQ=WEEKLY;'
        f'UNTIL={next_year}0620T220000Z;'
        'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    assert [o.start.day for o in event.occurrences] == [16, 17, 18, 19, 20]
    assert sorted(event.tags) == ['animals', 'fun']
    assert event.coordinates.lat
    assert int(event.coordinates.lat) == 47
    assert event.coordinates.lon
    assert int(event.coordinates.lon) == 8

    # date
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Virsit',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART;VALUE=DATE:{next_year}0616',
        f'DTEND;VALUE=DATE:{next_year}0616',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0616T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Par',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.start == tzdatetime(next_year, 6, 16, 0, 0, 'Europe/Zurich')
    assert event.end == tzdatetime(next_year, 6, 16, 23, 59, 'Europe/Zurich')

    # relative date-time
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Visit',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART:{next_year}0616T133000',
        f'DTEND:{next_year}0616T220000',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0616T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.start == tzdatetime(next_year, 6, 16, 13, 30, 'Europe/Zurich')
    assert event.end == tzdatetime(next_year, 6, 16, 22, 0, 'Europe/Zurich')

    # start and duration
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:Squirrel Park Visit',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART:{next_year}0616T133000',
        'DURATION:PT8H30M',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0616T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.start == tzdatetime(next_year, 6, 16, 13, 30, 'Europe/Zurich')
    assert event.end == tzdatetime(next_year, 6, 16, 22, 0, 'Europe/Zurich')

    # escape of title, description, location and organizer
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:<b>Squirrel Park Virsit</b>',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART;VALUE=DATE:{next_year}0616',
        f'DTEND;VALUE=DATE:{next_year}0616',
        'DTSTAMP:20140101T000000Z',
        (
            'RRULE:FREQ=WEEKLY;'
            f'UNTIL={next_year}0616T220000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'CATEGORIES:fun,animals',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:<i>Squirrel Par</i>',
        'ORGANIZER:<Super ME>',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.title == '&lt;b&gt;Squirrel Park Virsit&lt;/b&gt;'
    assert event.description == \
           '&lt;em&gt;Furri&lt;/em&gt; things will happen!'
    assert event.location == '&lt;i&gt;Squirrel Par&lt;/i&gt;'
    assert event.organizer == '&lt;Super ME&gt;'

    # empty category
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:<b>Squirrel Park Tour</b>',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART;VALUE=DATE:{next_year}0616',
        f'DTEND;VALUE=DATE:{next_year}0616',
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'CATEGORIES:',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:<i>Squirrel Par</i>',
        'ORGANIZER:<Super ME>',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]))
    transaction.commit()
    event = events.query().one()
    assert event.tags == []

    # no category -> default category
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:<b>Squirrel Park Tour</b>',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART;VALUE=DATE:{next_year}0616',
        f'DTEND;VALUE=DATE:{next_year}0616',
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:<i>Squirrel Par</i>',
        'ORGANIZER:<Super ME>',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]), default_categories=['Sport'])
    transaction.commit()
    event = events.query().one()
    assert sorted(event.tags) == ['Sport']
    assert event.filter_keywords == None

    # default keywords
    events.from_ical('\n'.join([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'SUMMARY:<b>Squirrel Park Tour</b>',
        'UID:squirrel-park-visit@onegov.event',
        f'DTSTART;VALUE=DATE:{next_year}0616',
        f'DTEND;VALUE=DATE:{next_year}0616',
        'DESCRIPTION:<em>Furri</em> things will happen!',
        'LAST-MODIFIED:20140101T000000Z',
        'LOCATION:<i>Squirrel Par</i>',
        'ORGANIZER:<Super ME>',
        'GEO:48.051752750515746;9.305739625357093',
        'URL:https://example.org/event/squirrel-park-visit',
        'END:VEVENT',
        'END:VCALENDAR'
    ]), default_filter_keywords={'kalender': ['Sport Veranstaltungskalender']})
    transaction.commit()
    event = events.query().one()
    assert sorted(event.tags) == []
    assert event.filter_keywords == {
        'kalender': ['Sport Veranstaltungskalender']}


def test_as_anthrazit_xml(session: Session) -> None:
    events = EventCollection(session)
    event = events.add(
        title='Squirrel Park Visit',
        start=datetime(2023, 4, 10, 9, 30),
        end=datetime(2023, 4, 10, 18, 00),
        timezone='Europe/Zurich',
        content={
            'description': 'Furry\r\nthings will happen!'
        },
        location='Squirrel Park',
        tags=['fun', 'animals'],
        filter_keywords=dict(EventType='Park'),
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU;'
            'UNTIL=20230420T220000Z'
        ),
        organizer_email='info@squirrelpark.com',
        organizer_phone='+1 123 456 7788',
        price='Adults: $12\r\nKids (>8): $4',
        coordinates=Coordinates(47.051752750515746, 8.305739625357093)
    )
    event.submit()
    event.publish()

    event = events.add(
        title='History of the Squirrel Park',
        start=datetime(2023, 4, 18, 14, 00),
        end=datetime(2023, 4, 18, 16, 00),
        timezone='Europe/Zurich',
        content={
            'description': 'Learn how the Park got so <em>furry</em>!'
        },
        location='Squirrel Park',
        tags=['history'],
        filter_keywords=dict(kalender='Park Calendar'),
    )
    event.submit()
    event.publish()

    session.flush()

    collection = EventCollection(session)
    xml = collection.as_anthrazit_xml(DummyRequest(),  # type: ignore[arg-type]
                                      future_events_only=False)

    import xml.etree.ElementTree as ET
    from lxml.etree import XMLParser

    parser = XMLParser(strip_cdata=False)
    root = ET.fromstring(xml, parser)  # type: ignore[arg-type]
    assert len(root) == 2

    # park opening
    expected_dates_start = [
        '2023-04-10 09:30:00',
        '2023-04-11 09:30:00',
        '2023-04-12 09:30:00',
        '2023-04-13 09:30:00',
        '2023-04-14 09:30:00',
        '2023-04-15 09:30:00',
        '2023-04-16 09:30:00',
        '2023-04-17 09:30:00',
        '2023-04-18 09:30:00',
        '2023-04-19 09:30:00',
        '2023-04-20 09:30:00',
    ]
    expected_dates_end = [
        '2023-04-10 18:00:00',
        '2023-04-11 18:00:00',
        '2023-04-12 18:00:00',
        '2023-04-13 18:00:00',
        '2023-04-14 18:00:00',
        '2023-04-15 18:00:00',
        '2023-04-16 18:00:00',
        '2023-04-17 18:00:00',
        '2023-04-18 18:00:00',
        '2023-04-19 18:00:00',
        '2023-04-20 18:00:00',
    ]
    assert root[0].attrib.keys() == ['status', 'suchbar', 'mutationsdatum']
    assert root[0].find('id').text  # type: ignore[union-attr]
    assert root[0].find('titel').text == 'Squirrel Park Visit'  # type: ignore[union-attr]
    # FYI CDATA gets stripped
    assert (root[0].find('textmobile').text == 'Furry<br>things will happen!')  # type: ignore[union-attr]
    dates = root[0].findall('termin')
    assert len(dates) == len(expected_dates_start)
    assert len(dates) == len(expected_dates_end)
    for d in dates:
        assert d.find('von').text in expected_dates_start  # type: ignore[operator, union-attr]
        assert d.find('bis').text in expected_dates_end  # type: ignore[operator, union-attr]
    assert root[0].find('hauptrubrik').attrib == {}  # type: ignore[union-attr]
    for rubrik in root[0].find('hauptrubrik').findall('rubrik'):  # type: ignore[union-attr]
        assert rubrik.text.lower() in ['fun', 'animals', 'park']  # type: ignore[union-attr]
    assert root[0].find('email').text == 'info@squirrelpark.com'  # type: ignore[union-attr]
    assert root[0].find('telefon1').text == '+1 123 456 7788'  # type: ignore[union-attr]
    assert root[0].find('sf01').text == 'Adults: $12<br>Kids (>8): $4'  # type: ignore[union-attr]
    assert root[0].find('veranstaltungsort').find('titel').text == ('Squirrel '  # type: ignore[union-attr]
                                                                    'Park')
    assert (root[0].find('veranstaltungsort').find('longitude').  # type: ignore[union-attr]
            text == '8.305739625357093')
    assert (root[0].find('veranstaltungsort').find('latitude').  # type: ignore[union-attr]
            text == '47.051752750515746')

    # history event
    assert root[1].attrib.keys() == ['status', 'suchbar', 'mutationsdatum']
    assert root[1].find('id').text  # type: ignore[union-attr]
    assert root[1].find('titel').text == 'History of the Squirrel Park'  # type: ignore[union-attr]
    assert (root[1].find('textmobile').text == 'Learn how the Park '  # type: ignore[union-attr]
                                               'got so <em>furry</em>!')
    assert (root[1].find('termin').find('von').  # type: ignore[union-attr]
            text == '2023-04-18 14:00:00')
    assert (root[1].find('termin').find('bis').  # type: ignore[union-attr]
            text == '2023-04-18 16:00:00')
    # test special case 'kalender' keyword
    assert root[1].find('hauptrubrik').attrib['name'] == 'Park Calendar'  # type: ignore[union-attr]
    for rubrik in root[1].find('hauptrubrik').findall('rubrik'):  # type: ignore[union-attr]
        assert rubrik.text in ['history']
    assert root[1].find('email') is None
    assert root[1].find('telefon1') is None
    assert root[1].find('sf01') is None
    assert root[1].find('veranstaltungsort').find('titel').text == ('Squirrel '  # type: ignore[union-attr]
                                                                    'Park')
    assert root[1].find('veranstaltungsort').find('longitude') is None  # type: ignore[union-attr]
    assert root[1].find('veranstaltungsort').find('latitude') is None  # type: ignore[union-attr]
