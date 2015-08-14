from datetime import date, datetime, timedelta
from mock import patch
from onegov.event import EventCollection, Occurrence, OccurrenceCollection
from sedate import replace_timezone, standardize_date


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_event_collection(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
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
            tags='fun, animals',
            recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5'
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
            tags='history'
        )
        event_2.submit()
        event_2.publish()
        assert events.query().count() == 2

        events.delete(event_1)
        events.delete(event_2)
        assert events.query().count() == 0
        assert session.query(Occurrence).count() == 0


def test_event_collection_remove_old_events(session):
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


def test_event_collection_pagination(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
        events = EventCollection(session)

        assert events.page_index == 0
        assert events.pages_count == 0
        assert events.batch == []

        for year in range(2008, 2011):
            for month in range(1, 13):
                event = events.add(
                    title='Event {0}-{1}'.format(year, month),
                    start=datetime(year, month, 18, 14, 00),
                    end=datetime(year, month, 18, 16, 00),
                    timezone='US/Eastern',
                    tags='year-{0}, month-{1}'.format(year, month),
                    recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
                )
                event.submit()
                if year > 2008:
                    event.publish()
                if year > 2009:
                    event.withdraw()
        assert events.query().count() == 3*12

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


def test_occurrence_collection(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
        event = EventCollection(session).add(
            title='Squirrel Park Visit',
            start=datetime(2015, 6, 16, 9, 30),
            end=datetime(2015, 6, 16, 18, 00),
            timezone='Pacific/Auckland',
            content={
                'description': '<em>Furry</em> things will happen!'
            },
            location='Squirrel Park',
            tags='fun, park, animals',
            recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5'
        )
        event.submit()
        event.publish()
        event = EventCollection(session).add(
            title='History of the Squirrel Park',
            start=datetime(2015, 6, 18, 14, 00),
            end=datetime(2015, 6, 18, 16, 00),
            timezone='Europe/Zurich',
            content={
                'description': 'Learn how the Park got so <em>furry</em>!'
            },
            location='Squirrel Park',
            tags='history'
        )
        event.submit()
        event.publish()

        occurrences = OccurrenceCollection(session)

        timezones = occurrences.used_timezones
        assert sorted(timezones) == ['Europe/Zurich', 'Pacific/Auckland']

        tags = occurrences.used_tags
        assert sorted(tags) == ['animals', 'fun', 'history', 'park']

        assert occurrences.query().count() == 6

        assert occurrences.query(tags=['animals']).count() == 5
        assert occurrences.query(tags=['park']).count() == 5
        assert occurrences.query(tags=['park', 'fun']).count() == 5
        assert occurrences.query(tags=['history']).count() == 1
        assert occurrences.query(tags=['history', 'fun']).count() == 6
        assert occurrences.query(tags=[]).count() == 6

        assert occurrences.query(start=date(2015, 6, 17)).count() == 5
        assert occurrences.query(start=date(2015, 6, 18)).count() == 4
        assert occurrences.query(start=date(2015, 6, 19)).count() == 2

        assert occurrences.query(end=date(2015, 6, 19)).count() == 5
        assert occurrences.query(end=date(2015, 6, 18)).count() == 4
        assert occurrences.query(end=date(2015, 6, 17)).count() == 2

        assert occurrences.query(start=date(2015, 6, 17),
                                 end=date(2015, 6, 18)).count() == 3
        assert occurrences.query(start=date(2015, 6, 18),
                                 end=date(2015, 6, 18)).count() == 2

        assert occurrences.query(start=date(2015, 6, 18),
                                 end=date(2015, 6, 18),
                                 tags=['history']).count() == 1


# for_filter
def test_occurrence_collection_pagination(session):
    with patch.object(EventCollection, 'remove_old_events') as mock_method:
        timezone = 'US/Eastern'

        occurrences = OccurrenceCollection(session)
        assert occurrences.page_index == 0
        assert occurrences.pages_count == 0
        assert occurrences.batch == []

        for year in range(2008, 2011):
            for month in range(1, 13):
                event = EventCollection(session).add(
                    title='Event {0}-{1}'.format(year, month),
                    start=datetime(year, month, 18, 14, 00),
                    end=datetime(year, month, 18, 16, 00),
                    timezone='US/Eastern',
                    tags='year-{0}, month-{1}'.format(year, month),
                    recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
                )
                event.submit()
                if year > 2008:
                    event.publish()
                if year > 2009:
                    event.withdraw()

        assert occurrences.query().count() == 4*12

        occurrences = OccurrenceCollection(session)
        assert occurrences.subset_count == 48
        assert all([o.start.year == 2009 for o in occurrences.batch])

        occurrences = OccurrenceCollection(session, start=date(2009, 12, 1))
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 12
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(session, end=date(2009, 1, 31))
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 1
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(session, start=date(2009, 5, 1),
                                           end=date(2009, 6, 30))
        assert occurrences.subset_count == 8
        assert all([o.start.year == 2009 and o.start.month in [5, 6]
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(session,
                                           tags=['month-7', 'month-8'])
        assert occurrences.subset_count == 8
        assert all([o.start.year == 2009 and o.start.month in [7, 8]
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(session, start=date(2009, 5, 1),
                                           end=date(2009, 6, 30),
                                           tags=['month-6'])
        assert occurrences.subset_count == 4
        assert all([o.start.year == 2009 and o.start.month == 6
                    for o in occurrences.batch])

        occurrences = OccurrenceCollection(session).for_filter()
        assert occurrences.start is None
        assert occurrences.end is None
        assert occurrences.tags == []

        occurrences = OccurrenceCollection(session, start=date(2009, 5, 1),
                                           end=date(2009, 6, 30),
                                           tags=['month-6']).for_filter()
        assert occurrences.start == date(2009, 5, 1)
        assert occurrences.end == date(2009, 6, 30)
        assert occurrences.tags == ['month-6']

        occurrences = occurrences.for_filter(start=date(2010, 5, 1))
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end == date(2009, 6, 30)
        assert occurrences.tags == ['month-6']

        occurrences = occurrences.for_filter(end=None)
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end is None
        assert occurrences.tags == ['month-6']

        occurrences = occurrences.for_filter(tags=[])
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end is None
        assert occurrences.tags == []

        occurrences = occurrences.for_filter(tags=['a', 'b'])
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end is None
        assert occurrences.tags == ['a', 'b']

        occurrences = occurrences.for_filter(tag='c')
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end is None
        assert occurrences.tags == ['a', 'b', 'c']

        occurrences = occurrences.for_filter(tag='a')
        assert occurrences.start == date(2010, 5, 1)
        assert occurrences.end is None
        assert occurrences.tags == ['b', 'c']
