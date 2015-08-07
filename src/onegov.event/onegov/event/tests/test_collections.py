from datetime import datetime
from onegov.event import EventCollection, OccurrenceCollection
from sedate import replace_timezone


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_collections(session):
    timezone = 'US/Eastern'

    events = EventCollection(session)
    occurrences = OccurrenceCollection(session)

    assert events.query().count() == 0
    assert occurrences.query().count() == 0

    event_1 = events.add(
        title='Squirrel Park Visit',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
        timezone=timezone,
        content={
            'description': 'Amuse yourself! <em>Furry</em> things will happen!'
        },
        location='Squirrel Park',
        tags='fun, animals',
        recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5'
    )
    event_1.submit()
    event_1.publish()
    event_2 = events.add(
        title='History of the Squirrel Park',
        start=datetime(2015, 6, 18, 14, 00),
        end=datetime(2015, 6, 18, 16, 00),
        timezone=timezone,
        content={
            'description': 'Learn how the Squirrel Park got so <em>furry</em>!'
        },
        location='Squirrel Park',
        tags='history'
    )
    event_2.submit()
    event_2.publish()
    assert events.query().count() == 2
    assert occurrences.query().count() == 6

    assert occurrences.query(tags=['fun']).count() == 5
    assert occurrences.query(tags=['fun', 'history']).count() == 6
    assert occurrences.query(tags=['animals', 'history']).count() == 6
    assert occurrences.query(tags=['history']).count() == 1

    assert occurrences.query(
        start=tzdatetime(2015, 7, 1, 0, 0, timezone)
    ).count() == 0
    assert occurrences.query(
        start=tzdatetime(2015, 6, 19, 0, 0, timezone)
    ).count() == 2
    assert occurrences.query(
        end=tzdatetime(2015, 6, 1, 0, 0, timezone)
    ).count() == 0
    assert occurrences.query(
        end=tzdatetime(2015, 6, 17, 23, 59, timezone)
    ).count() == 2
    assert occurrences.query(
        start=tzdatetime(2015, 6, 17, 0, 0, timezone),
        end=tzdatetime(2015, 6, 19, 23, 59, timezone)
    ).count() == 4

    events.delete(event_1)
    events.delete(event_2)
    assert events.query().count() == 0
    assert occurrences.query().count() == 0
