from datetime import datetime, timedelta
from mock import patch
from onegov.event import EventCollection, OccurrenceCollection
from sedate import replace_timezone, standardize_date


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_collections(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
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
                'description': '<em>Furry</em> things will happen!'
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
                'description': 'Learn how the Park got so <em>furry</em>!'
            },
            location='Squirrel Park',
            tags='history'
        )
        event_2.submit()
        event_2.publish()
        assert events.query().count() == 2
        assert occurrences.query().count() == 6

        assert occurrences.query().all() == sorted(
            occurrences.query().all(), key=lambda x: x.start
        )

        assert sorted(occurrences.used_tags) == ['animals', 'fun', 'history']

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


def test_paginations(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
        timezone = 'US/Eastern'

        events = EventCollection(session)
        occurrences = OccurrenceCollection(session)

        assert events.page_index == 0
        assert events.pages_count == 0
        assert events.batch == []
        assert occurrences.page_index == 0
        assert occurrences.pages_count == 0
        assert occurrences.batch == []

        for year in range(2008, 2011):
            for month in range(1, 13):
                event = events.add(
                    title='Event {0}-{1}'.format(year, month),
                    start=datetime(year, month, 18, 14, 00),
                    end=datetime(year, month, 18, 16, 00),
                    timezone=timezone,
                    tags='year-{0}, month-{1}'.format(year, month),
                    recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
                )
                event.submit()
                if year > 2008:
                    event.publish()
                if year > 2009:
                    event.withdraw()
        assert events.query().count() == 3*12
        assert occurrences.query().count() == 4*12

        events = EventCollection(session, state='initiated')
        assert events.subset_count == 0

        events = EventCollection(session, state='submitted')
        assert events.subset_count == 12
        assert all([e.start.year == 2008 for e in events.batch])
        assert all([e.start.month < 11 for e in events.batch])
        assert len(events.next.batch) == 12 - events.batch_size
        assert all([e.start.year == 2008 for e in events.next.batch])
        assert all([e.start.month > 10 for e in events.next.batch])

        events = EventCollection(session, state='published')
        assert events.subset_count == 12
        assert all([e.start.year == 2009 for e in events.batch])
        assert all([e.start.month < 11 for e in events.batch])
        assert len(events.next.batch) == 12 - events.batch_size
        assert all([e.start.year == 2009 for e in events.next.batch])
        assert all([e.start.month > 10 for e in events.next.batch])

        events = EventCollection(session, state='withdrawn')
        assert events.subset_count == 12
        assert all([e.start.year == 2010 for e in events.batch])
        assert all([e.start.month < 11 for e in events.batch])
        assert len(events.next.batch) == 12 - events.batch_size
        assert all([e.start.year == 2010 for e in events.next.batch])
        assert all([e.start.month > 10 for e in events.next.batch])

        occurrences = OccurrenceCollection(session)
        assert occurrences.subset_count == 48
        assert all([o.start.year == 2009 for o in occurrences.batch])

        occurrences = OccurrenceCollection(
            session, start=tzdatetime(2009, 12, 1, 0, 0, timezone)
        )
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 12
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(
            session, end=tzdatetime(2009, 1, 31, 0, 0, timezone)
        )
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 1
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(
            session, start=tzdatetime(2009, 5, 1, 0, 0, timezone),
            end=tzdatetime(2009, 6, 30, 0, 0, timezone)
        )
        assert occurrences.subset_count == 8
        assert all([o.start.year == 2009 and o.start.month in [5, 6]
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(
            session, tags=['month-7', 'month-8']
        )
        assert occurrences.subset_count == 8
        assert all([o.start.year == 2009 and o.start.month in [7, 8]
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(
            session, start=tzdatetime(2009, 5, 1, 0, 0, timezone),
            end=tzdatetime(2009, 6, 30, 0, 0, timezone), tags=['month-6']
        )
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 6
                    for o in occurrences.batch])


def test_remove_old_events(session):
    timezone = 'UTC'

    with patch.object(EventCollection, 'remove_old_events') as mock_method:
        events = EventCollection(session)
        event_dates = (
            (datetime(2015, 6, 1, 10), ''),
            (datetime(2015, 6, 1, 11), 'RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=3'),
            (datetime(2015, 6, 1, 12), 'RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=6'),
            (datetime(2015, 7, 1, 13), ''),
            (datetime(2015, 7, 1, 14), 'RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=4'),
            (datetime(2015, 7, 25, 15), ''),
        )

        for date, rrule in event_dates:
            event = events.add(title='Event', timezone=timezone, start=date,
                               end=date + timedelta(hours=1), recurrence=rrule)
            event.submit()
        for date, rrule in event_dates:
            event = events.add(title='Event', timezone=timezone, start=date,
                               end=date + timedelta(hours=1), recurrence=rrule)
            event.submit()
            event.publish()
        for date, rrule in event_dates:
            event = events.add(title='Event', timezone=timezone, start=date,
                               end=date + timedelta(hours=1), recurrence=rrule)
            event.submit()
            event.publish()
            event.withdraw()

    events = EventCollection(session)

    max_age = standardize_date(datetime(2015, 7, 1), 'UTC')
    events.remove_old_events(max_age=max_age)
    assert events.query().count() == 4*3

    max_age = standardize_date(datetime(2015, 7, 20), 'UTC')
    events.remove_old_events(max_age=max_age)
    assert events.query().count() == 2*3

    max_age = standardize_date(datetime(2015, 8, 1), 'UTC')
    events.remove_old_events(max_age=max_age)
    assert events.query().count() == 0

    event = events.add(
        title='Event', timezone=timezone,
        start=datetime(2010, 6, 1, 10),
        end=datetime(2010, 6, 1, 10) + timedelta(hours=1),
    )
    assert events.query().count() == 0
