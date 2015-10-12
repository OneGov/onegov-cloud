from datetime import date, datetime, timedelta
from onegov.event import EventCollection, Occurrence, OccurrenceCollection
from sedate import replace_timezone, standardize_date


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_event_collection(session):
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
        tags=['history']
    )
    event_2.submit()
    event_2.publish()
    assert events.query().count() == 2

    events.delete(event_1)
    events.delete(event_2)
    assert events.query().count() == 0
    assert session.query(Occurrence).count() == 0


def test_event_collection_remove_stale_events(session):
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


def test_event_collection_pagination(session):
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
                tags=['month-{0}'.format(month)],
                recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
            )
            event.submit()
            if year > 2008:
                event.publish()
            if year > 2009:
                event.withdraw()
    assert events.query().count() == 3 * 12

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
    event = EventCollection(session).add(
        title='Squirrel Park Visit',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
        timezone='Pacific/Auckland',
        content={
            'description': '<em>Furry</em> things will happen!'
        },
        location='Squirrel Park',
        tags=['fun', 'park', 'animals'],
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
        tags=['history']
    )
    event.submit()
    event.publish()

    occurrences = OccurrenceCollection(session)

    timezones = occurrences.used_timezones
    assert sorted(timezones) == ['Europe/Zurich', 'Pacific/Auckland']

    tags = occurrences.used_tags
    assert sorted(tags) == ['animals', 'fun', 'history', 'park']

    def query(**kwargs):
        return occurrences.query(outdated=True, **kwargs)

    assert query().count() == 6

    assert query(tags=['animals']).count() == 5
    assert query(tags=['park']).count() == 5
    assert query(tags=['park', 'fun']).count() == 5
    assert query(tags=['history']).count() == 1
    assert query(tags=['history', 'fun']).count() == 6
    assert query(tags=[]).count() == 6

    assert query(start=date(2015, 6, 17)).count() == 5
    assert query(start=date(2015, 6, 18)).count() == 4
    assert query(start=date(2015, 6, 19)).count() == 2

    assert query(end=date(2015, 6, 19)).count() == 5
    assert query(end=date(2015, 6, 18)).count() == 4
    assert query(end=date(2015, 6, 17)).count() == 2

    assert query(start=date(2015, 6, 17), end=date(2015, 6, 18)).count() == 3
    assert query(start=date(2015, 6, 18), end=date(2015, 6, 18)).count() == 2

    assert query(start=date(2015, 6, 18), end=date(2015, 6, 18),
                 tags=['history']).count() == 1


def test_occurrence_collection_pagination(session):

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
                tags=['month-{0}'.format(month)],
                recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=4'
            )
            event.submit()
            if year > 2008:
                event.publish()
            if year > 2009:
                event.withdraw()

    class PatchedCollection(OccurrenceCollection):
        def query(self, **kwargs):
            return super().query(outdated=True, **kwargs)

    occurrences = PatchedCollection(session)
    assert occurrences.query().count() == 4 * 12

    occurrences = PatchedCollection(session)
    assert occurrences.subset_count == 48
    assert all([o.start.year == 2009 for o in occurrences.batch])

    occurrences = PatchedCollection(session, start=date(2009, 12, 1))
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 12
                for o in occurrences.batch])

    occurrences = PatchedCollection(session, end=date(2009, 1, 31))
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 1
                for o in occurrences.batch])

    occurrences = PatchedCollection(session,
                                    start=date(2009, 5, 1),
                                    end=date(2009, 6, 30))
    assert occurrences.subset_count == 8
    assert all([o.start.year == 2009 and o.start.month in [5, 6]
                for o in occurrences.batch])

    occurrences = PatchedCollection(session, tags=['month-7', 'month-8'])

    assert occurrences.subset_count == 8
    assert all([o.start.year == 2009 and o.start.month in [7, 8]
                for o in occurrences.batch])

    occurrences = PatchedCollection(session,
                                    start=date(2009, 5, 1),
                                    end=date(2009, 6, 30),
                                    tags=['month-6'])
    assert occurrences.subset_count == 4
    assert all([o.start.year == 2009 and o.start.month == 6
                for o in occurrences.batch])

    occurrences = PatchedCollection(session).for_filter()
    assert occurrences.start is None
    assert occurrences.end is None
    assert occurrences.tags == []

    occurrences = PatchedCollection(session,
                                    start=date(2009, 5, 1),
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


def test_occurrence_collection_outdated(session):
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

    occurrences = OccurrenceCollection(session)
    assert occurrences.query().count() == 2
    assert occurrences.query(outdated=True).count() == 3
    assert occurrences.query(start=date(today.year - 1, 1, 1)).count() == 3
    assert occurrences.query(start=date(today.year - 1, 1, 1)).count() == 3


def test_unique_names(session):
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
        recurrence='RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5'
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


def test_unicode(session):
    event = EventCollection(session).add(
        title='Salon du mieux-vivre, 16e édition',
        start=datetime(2015, 6, 16, 9, 30),
        end=datetime(2015, 6, 16, 18, 00),
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
        start=datetime(2015, 6, 18, 14, 00),
        end=datetime(2015, 6, 18, 16, 00),
        timezone='Europe/Zurich',
        content={
            'description': 'Congrès en français et espagnol.'
        },
        location='Salon du mieux-vivre à Saignelégier',
        tags=['témoins']
    )
    event.submit()
    event.publish()

    occurrences = OccurrenceCollection(session)

    assert occurrences.query(outdated=True).count() == 2

    tags = occurrences.used_tags
    assert sorted(tags) == ['congrès', 'salons', 'témoins']

    occurrence = occurrences.query(outdated=True, tags=['congrès']).one()
    assert occurrence.title == 'Salon du mieux-vivre, 16e édition'
    assert occurrence.location == 'Salon du mieux-vivre à Saignelégier'
    assert sorted(occurrence.tags) == ['congrès', 'salons']
    assert occurrence.event.description \
        == 'Rendez-vous automnal des médecines.'

    occurrence = occurrences.query(outdated=True, tags=['témoins']).one()
    assert occurrence.title == 'Témoins de Jéhovah'
    assert occurrence.location == 'Salon du mieux-vivre à Saignelégier'
    assert occurrence.tags == ['témoins']
    assert occurrence.event.description == 'Congrès en français et espagnol.'
