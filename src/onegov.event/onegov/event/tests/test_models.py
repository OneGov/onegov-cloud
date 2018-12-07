import pytest
import transaction

from datetime import datetime
from datetime import timedelta
from io import BytesIO
from onegov.core.utils import module_path
from onegov.event import Event
from onegov.event import Occurrence
from onegov.event.utils import as_rdates
from onegov.gis import Coordinates
from pytest import mark
from sedate import replace_timezone


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_transitions():

    event = Event(state='initiated')
    assert event.state == 'initiated'

    with pytest.raises(AssertionError):
        event.publish()
    with pytest.raises(AssertionError):
        event.withdraw()
    event.submit()
    assert event.state == 'submitted'

    with pytest.raises(AssertionError):
        event.submit()
    with pytest.raises(AssertionError):
        event.withdraw()
    event.publish()
    assert event.state == 'published'

    with pytest.raises(AssertionError):
        event.submit()
    with pytest.raises(AssertionError):
        event.publish()
    event.withdraw()
    assert event.state == 'withdrawn'

    with pytest.raises(AssertionError):
        event.submit()
    with pytest.raises(AssertionError):
        event.withdraw()
    event.publish()
    assert event.state == 'published'


def test_create_event(session):
    start = tzdatetime(2008, 2, 7, 10, 15, 'Europe/Zurich')
    end = tzdatetime(2008, 2, 7, 16, 00, 'Europe/Zurich')

    event = Event(state='initiated')
    event.timezone = 'Europe/Zurich'
    event.start = start
    event.end = end
    event.recurrence = None
    event.title = 'Squirrel Park Visit'
    event.description = '<em>Furry</em> things will happen!'
    event.organizer = 'Squirrel Park'
    event.location = 'Squirrel Park'
    event.tags = ['fun', 'animals', 'furry']
    event.meta = {'submitter': 'fat.pauly@squirrelpark.org'}
    event.source = 'source'
    event.source_updated = 'now'
    event.name = 'event'
    session.add(event)

    event.submit()
    event.publish()

    transaction.commit()  # make sure the dates are converted to UTC

    event = session.query(Event).one()
    assert event.timezone == 'Europe/Zurich'
    assert event.start == start
    assert event.localized_start == start
    assert str(event.start.tzinfo) == 'UTC'
    assert str(event.localized_start.tzinfo) == 'Europe/Zurich'
    assert event.end == end
    assert event.localized_end == end
    assert str(event.end.tzinfo) == 'UTC'
    assert str(event.localized_end.tzinfo) == 'Europe/Zurich'
    assert event.recurrence == None
    assert event.title == 'Squirrel Park Visit'
    assert event.location == 'Squirrel Park'
    assert sorted(event.tags) == sorted(['fun', 'animals', 'furry'])
    assert event.description == '<em>Furry</em> things will happen!'
    assert event.organizer == 'Squirrel Park'
    assert event.meta['submitter'] == 'fat.pauly@squirrelpark.org'
    assert event.source == 'source'
    assert event.source_updated == 'now'
    assert event.name == 'event'

    occurrence = session.query(Occurrence).one()
    assert occurrence.timezone == 'Europe/Zurich'
    assert occurrence.start == start
    assert occurrence.localized_start == start
    assert str(occurrence.start.tzinfo) == 'UTC'
    assert str(occurrence.localized_start.tzinfo) == 'Europe/Zurich'
    assert occurrence.end == end
    assert occurrence.localized_end == end
    assert str(occurrence.end.tzinfo) == 'UTC'
    assert str(occurrence.localized_end.tzinfo) == 'Europe/Zurich'
    assert occurrence.title == 'Squirrel Park Visit'
    assert occurrence.location == 'Squirrel Park'
    assert sorted(occurrence.tags) == sorted(['fun', 'animals', 'furry'])
    assert occurrence.event.description == '<em>Furry</em> things will happen!'
    assert occurrence.name == 'event-2008-02-07'

    assert [o.id for o in event.occurrences] == [occurrence.id]
    assert occurrence.event.id == event.id


@mark.parametrize("path", [module_path('onegov.event', 'tests/fixtures')])
def test_event_image(test_app, path):
    session = test_app.session()

    event = Event(state='initiated')
    event.timezone = 'Europe/Zurich'
    event.start = tzdatetime(2008, 2, 7, 10, 15, 'Europe/Zurich')
    event.end = tzdatetime(2008, 2, 7, 16, 00, 'Europe/Zurich')
    event.title = 'Squirrel Park Visit'
    session.add(event)
    event.submit()
    event = session.query(Event).one()

    assert event.image == None

    with open(f'{path}/event.png', 'rb') as file:
        content = file.read()

    event.set_image(BytesIO(content), 'file.png')
    session.flush()
    assert event.image.reference.file.read() == content

    with open(f'{path}/event.jpg', 'rb') as file:
        content = file.read()

    event.set_image(BytesIO(content), 'file.png')
    session.flush()
    assert event.image.reference.file.read() == content

    event.set_image(None, None)
    session.flush()
    assert event.image == None


def test_occurrence_dates(session):
    year = datetime.today().year

    event = Event(state='initiated')
    event.timezone = 'Europe/Zurich'
    event.start = tzdatetime(year, 2, 7, 10, 15, 'Europe/Zurich')
    event.end = tzdatetime(year, 2, 7, 16, 00, 'Europe/Zurich')
    event.recurrence = (
        f'RRULE:FREQ=WEEKLY;'
        f'UNTIL={year+2}0211T100000Z;'
        f'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )

    assert len(event.occurrence_dates(limit=False)) > 700

    dates = event.occurrence_dates()
    assert len(dates) < 700
    assert dates[0] == tzdatetime(year, 2, 7, 10, 15, 'Europe/Zurich')
    assert dates[-1] == tzdatetime(year + 1, 12, 31, 10, 15, 'Europe/Zurich')
    assert str(dates[0].tzinfo) == 'UTC'
    assert str(dates[-1].tzinfo) == 'UTC'

    dates = event.occurrence_dates(localize=True)
    assert len(dates) < 700
    assert dates[0] == tzdatetime(year, 2, 7, 10, 15, 'Europe/Zurich')
    assert dates[-1] == tzdatetime(year + 1, 12, 31, 10, 15, 'Europe/Zurich')
    assert str(dates[0].tzinfo) == 'Europe/Zurich'
    assert str(dates[-1].tzinfo) == 'Europe/Zurich'

    event.title = 'Event'
    session.add(event)
    transaction.commit()

    event = session.query(Event).one()
    assert len(event.occurrence_dates(limit=False)) > 700

    dates = event.occurrence_dates()
    assert len(dates) < 700
    assert dates[0] == tzdatetime(year, 2, 7, 10, 15, 'Europe/Zurich')
    assert dates[-1] == tzdatetime(year + 1, 12, 31, 10, 15, 'Europe/Zurich')
    assert str(dates[0].tzinfo) == 'UTC'
    assert str(dates[-1].tzinfo) == 'UTC'

    dates = event.occurrence_dates(localize=True)
    assert len(dates) < 700
    assert dates[0] == tzdatetime(year, 2, 7, 10, 15, 'Europe/Zurich')
    assert dates[-1] == tzdatetime(year + 1, 12, 31, 10, 15, 'Europe/Zurich')
    assert str(dates[0].tzinfo) == 'Europe/Zurich'
    assert str(dates[-1].tzinfo) == 'Europe/Zurich'


def test_latest_occurrence(session):

    def create_event(delta):
        start = datetime.now() + delta
        end = start + timedelta(hours=6)
        session.query(Occurrence).delete()
        session.query(Event).delete()
        session.add(
            Event(
                state='published',
                title='Event',
                timezone='Europe/Zurich',
                start=replace_timezone(start, 'Europe/Zurich'),
                end=replace_timezone(end, 'Europe/Zurich'),
                recurrence=(
                    f'RRULE:FREQ=WEEKLY;'
                    f'UNTIL={end.year}{end.month:02}{end.day:02}T220000Z;'
                    f'BYDAY=MO,TU,WE,TH,FR,SA,SU'
                ),
            )
        )
        transaction.commit()
        return session.query(Event).one()

    # current
    event = create_event(timedelta(hours=-3))
    assert event.latest_occurrence.start == event.occurrence_dates()[0]

    event = create_event(timedelta(days=-1, hours=-3))
    assert event.latest_occurrence.start == event.occurrence_dates()[1]

    # past
    event = create_event(timedelta(days=-40))
    assert event.latest_occurrence.start == event.occurrence_dates()[-1]

    # future
    event = create_event(timedelta(days=40))
    assert event.latest_occurrence.start == event.occurrence_dates()[0]


def test_occurrence_dates_dst(session):
    year = datetime.today().year

    event = Event(state='initiated')
    event.timezone = 'Europe/Zurich'
    event.start = tzdatetime(year, 1, 1, 10, 15, 'Europe/Zurich')
    event.end = tzdatetime(year, 1, 11, 16, 00, 'Europe/Zurich')

    with pytest.raises(RuntimeError) as e:
        event.recurrence = (
            f'RRULE:FREQ=WEEKLY;'
            f'UNTIL={year}12310000;'
            f'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        )

    assert 'UNTIL is not timezone-aware' in str(e)

    event.recurrence = (
        f'RRULE:FREQ=WEEKLY;'
        f'UNTIL={year}12310000Z;'
        f'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    occurrences = event.occurrence_dates(localize=True)
    assert all((o.hour == 10 for o in occurrences))


def test_create_event_recurring(session):
    timezone = 'Europe/Zurich'
    start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    end = tzdatetime(2008, 2, 7, 16, 00, timezone)
    title = 'Squirrel Park Visit'
    description = '<em>Furry</em> things will happen!'
    location = 'Squirrel Park'
    tags = ['fun', 'animals', 'furry']

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = start
    event.end = end
    event.recurrence = (
        'RRULE:FREQ=WEEKLY;'
        'UNTIL=200802111500Z;'
        'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    event.title = title
    event.content = {'description': description}
    event.location = location
    event.tags = tags
    event.meta = {'submitter': 'fat.pauly@squirrelpark.org'}
    event.name = 'event'
    session.add(event)

    event.submit()
    event.publish()

    transaction.commit()

    event = session.query(Event).one()
    assert event.timezone == timezone
    assert event.start == start
    assert event.localized_start == start
    assert str(event.start.tzinfo) == 'UTC'
    assert str(event.localized_start.tzinfo) == timezone
    assert event.end == end
    assert event.localized_end == end
    assert str(event.end.tzinfo) == 'UTC'
    assert str(event.localized_end.tzinfo) == timezone
    assert event.recurrence == (
        'RRULE:FREQ=WEEKLY;'
        'UNTIL=200802111500Z;'
        'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    assert event.title == title
    assert event.location == location
    assert sorted(event.tags) == sorted(tags)
    assert event.description == description
    assert event.content == {'description': description}
    assert event.meta == {'submitter': 'fat.pauly@squirrelpark.org'}
    assert event.name == 'event'

    occurrences = session.query(Occurrence).all()
    assert len(occurrences) == 5
    for occurrence in occurrences:
        assert occurrence.timezone == timezone
        assert str(occurrence.start.tzinfo) == 'UTC'
        assert str(occurrence.localized_start.tzinfo) == timezone
        assert str(occurrence.end.tzinfo) == 'UTC'
        assert str(occurrence.localized_end.tzinfo) == timezone
        assert occurrence.title == title
        assert occurrence.location == location
        assert sorted(occurrence.tags) == sorted(tags)
        assert occurrence.event.description == description

    assert occurrences[0].start == start
    assert occurrences[0].localized_start == start
    assert occurrences[0].end == end
    assert occurrences[0].localized_end == end
    assert occurrences[0].name == 'event-2008-02-07'

    start = tzdatetime(2008, 2, 8, 10, 15, timezone)
    end = tzdatetime(2008, 2, 8, 16, 00, timezone)
    assert occurrences[1].start == start
    assert occurrences[1].localized_start == start
    assert occurrences[1].end == end
    assert occurrences[1].localized_end == end
    assert occurrences[1].name == 'event-2008-02-08'

    start = tzdatetime(2008, 2, 9, 10, 15, timezone)
    end = tzdatetime(2008, 2, 9, 16, 00, timezone)
    assert occurrences[2].start == start
    assert occurrences[2].localized_start == start
    assert occurrences[2].end == end
    assert occurrences[2].localized_end == end
    assert occurrences[2].name == 'event-2008-02-09'

    start = tzdatetime(2008, 2, 10, 10, 15, timezone)
    end = tzdatetime(2008, 2, 10, 16, 00, timezone)
    assert occurrences[3].start == start
    assert occurrences[3].localized_start == start
    assert occurrences[3].end == end
    assert occurrences[3].localized_end == end
    assert occurrences[3].name == 'event-2008-02-10'

    start = tzdatetime(2008, 2, 11, 10, 15, timezone)
    end = tzdatetime(2008, 2, 11, 16, 00, timezone)
    assert occurrences[4].start == start
    assert occurrences[4].localized_start == start
    assert occurrences[4].end == end
    assert occurrences[4].localized_end == end
    assert occurrences[4].name == 'event-2008-02-11'

    assert (sorted([o.id for o in event.occurrences])
            == sorted([o.id for o in occurrences]))
    assert occurrences[0].event.id == event.id
    assert occurrences[1].event.id == event.id
    assert occurrences[2].event.id == event.id
    assert occurrences[3].event.id == event.id
    assert occurrences[4].event.id == event.id


def test_update_event(session):
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2008, 2, 7, 16, 00, timezone)
    event.title = 'Squirrel Park Visit'
    event.content = {'description': '<em>Furry</em> things will happen!'}
    event.location = 'Squirrel Park'
    event.tags = ['fun', 'animals', 'furry']
    event.name = 'event'
    session.add(event)

    event.submit()
    event.publish()

    occurence = session.query(Event).one().occurrences[0]
    assert occurence.timezone == event.timezone
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.title == event.title
    assert occurence.event.content == event.content
    assert occurence.event.description == event.content['description']
    assert occurence.event.location == event.location
    assert occurence.location == event.location
    assert sorted(occurence.event.tags) == sorted(event.tags)
    assert sorted(occurence.tags) == sorted(event.tags)
    assert occurence.name == 'event-2008-02-07'

    event.start = tzdatetime(2009, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2009, 2, 7, 10, 15, timezone)
    event.title = 'Squirrel Park Visit - Cancelled'
    event.content = {'description': 'No <em>Furry</em> things will happen! :('}
    event.location = '-'
    event.tags = ['no fun', 'no animals']

    assert len(session.query(Event).one().occurrences) == 1
    occurence = session.query(Event).one().occurrences[0]
    assert occurence.timezone == event.timezone
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.title == event.title
    assert occurence.event.content == event.content
    assert occurence.event.description == event.content['description']
    assert occurence.event.location == event.location
    assert occurence.location == event.location
    assert sorted(occurence.event.tags) == sorted(event.tags)
    assert sorted(occurence.tags) == sorted(event.tags)

    event.recurrence = (
        'RRULE:FREQ=WEEKLY;'
        'UNTIL=20090209T090000Z;'
        'BYDAY=MO,TU,WE,TH,FR,SA,SU'
    )
    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].start == tzdatetime(2009, 2, 7, 10, 15, timezone)
    assert occurrences[0].end == tzdatetime(2009, 2, 7, 10, 15, timezone)
    assert occurrences[1].start == tzdatetime(2009, 2, 8, 10, 15, timezone)
    assert occurrences[1].end == tzdatetime(2009, 2, 8, 10, 15, timezone)

    event.timezone = 'US/Eastern'
    assert session.query(Event).one().timezone == 'US/Eastern'

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].start == tzdatetime(2009, 2, 7, 10, 15, timezone)
    assert occurrences[0].end == tzdatetime(2009, 2, 7, 10, 15, timezone)
    assert occurrences[0].timezone == 'US/Eastern'
    assert occurrences[1].start == tzdatetime(2009, 2, 8, 10, 15, timezone)
    assert occurrences[1].end == tzdatetime(2009, 2, 8, 10, 15, timezone)
    assert occurrences[1].timezone == 'US/Eastern'

    event.name = 'new-event'
    assert session.query(Event).one().name == 'new-event'

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].name == 'new-event-2009-02-07'
    assert occurrences[1].name == 'new-event-2009-02-08'

    event.recurrence = ''
    assert session.query(Occurrence).count() == 1
    assert len(session.query(Event).one().occurrences) == 1


def test_delete_event(session):
    timezone = 'Europe/Zurich'
    event = Event(
        state='initiated',
        title='event',
        start=tzdatetime(2008, 2, 7, 10, 15, timezone),
        end=tzdatetime(2008, 2, 7, 16, 00, timezone),
        timezone=timezone
    )
    session.add(event)
    session.delete(session.query(Event).one())
    transaction.commit()
    session.expire_all()
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(
        state='initiated',
        title='event',
        start=tzdatetime(2008, 2, 7, 10, 15, timezone),
        end=tzdatetime(2008, 2, 7, 16, 00, timezone),
        timezone=timezone
    )
    session.add(event)
    event.submit()
    session.delete(session.query(Event).one())
    transaction.commit()
    session.expire_all()
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(
        state='initiated',
        title='event',
        start=tzdatetime(2008, 2, 7, 10, 15, timezone),
        end=tzdatetime(2008, 2, 7, 16, 00, timezone),
        timezone=timezone
    )
    session.add(event)
    event.submit()
    event.publish()
    session.delete(session.query(Event).one())
    transaction.commit()
    session.expire_all()
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(
        state='initiated',
        title='event',
        start=tzdatetime(2008, 2, 7, 10, 15, timezone),
        end=tzdatetime(2008, 2, 7, 16, 00, timezone),
        timezone=timezone
    )
    session.add(event)
    event.submit()
    event.publish()
    event.withdraw()
    session.delete(session.query(Event).one())
    transaction.commit()
    session.expire_all()
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0


def test_as_ical():
    url = 'https://example.org/my-event'
    event = Event(
        state='initiated',
        timezone='Europe/Zurich',
        start=tzdatetime(2008, 2, 7, 10, 15, 'Europe/Zurich'),
        end=tzdatetime(2008, 2, 7, 16, 00, 'Europe/Zurich'),
        recurrence=(
            'RRULE:FREQ=WEEKLY;'
            'UNTIL=20080207T150000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        title='Squirrel Park Visit',
        content={'description': '<em>Furry</em> things will happen!'},
        location='Squirrel Park',
        tags=['fun', 'animals', 'furry'],
        meta={'submitter': 'fat.pauly@squirrelpark.org'},
        name='event',
        modified=tzdatetime(2008, 2, 7, 10, 15, 'Europe/Zurich'),
        coordinates=Coordinates(47.051752750515746, 8.305739625357093)
    )
    ical = event.as_ical(url=url).decode().strip().splitlines()
    assert sorted(ical) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'UID:event-2008-02-07@onegov.event',
        'SUMMARY:Squirrel Park Visit',
        'DTSTART;VALUE=DATE-TIME:20080207T091500Z',
        'DTEND;VALUE=DATE-TIME:20080207T150000Z',
        'DTSTAMP;VALUE=DATE-TIME:20080207T091500Z',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals,furry',
        'LAST-MODIFIED;VALUE=DATE-TIME:20080207T091500Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        (
            'RRULE:FREQ=WEEKLY;'
            'UNTIL=20080207T150000Z;'
            'BYDAY=MO,TU,WE,TH,FR,SA,SU'
        ),
        'URL:https://example.org/my-event',
        'END:VEVENT',
        'END:VCALENDAR',
    ])

    event.submit()
    event.publish()
    occurrence = event.occurrences[0]
    occurrence.modified = tzdatetime(2008, 2, 7, 10, 15, 'Europe/Zurich')

    ical = event.occurrences[0].as_ical(url=url).decode().strip().splitlines()
    assert sorted(ical) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'UID:event-2008-02-07@onegov.event',
        'SUMMARY:Squirrel Park Visit',
        'DTSTART;VALUE=DATE-TIME:20080207T091500Z',
        'DTEND;VALUE=DATE-TIME:20080207T150000Z',
        'DTSTAMP;VALUE=DATE-TIME:20080207T091500Z',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals,furry',
        'LAST-MODIFIED;VALUE=DATE-TIME:20080207T091500Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/my-event',
        'END:VEVENT',
        'END:VCALENDAR',
    ])

    event.recurrence = as_rdates('FREQ=WEEKLY;COUNT=2', event.start)
    ical = event.as_ical(url=url).decode().strip().splitlines()
    assert sorted(ical) == sorted([
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//OneGov//onegov.event//',
        'BEGIN:VEVENT',
        'UID:event-2008-02-07@onegov.event',
        'SUMMARY:Squirrel Park Visit',
        'DTSTART;VALUE=DATE-TIME:20080207T091500Z',
        'DTEND;VALUE=DATE-TIME:20080207T150000Z',
        'DTSTAMP;VALUE=DATE-TIME:20080207T091500Z',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals,furry',
        'LAST-MODIFIED;VALUE=DATE-TIME:20080207T091500Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/my-event',
        'END:VEVENT',
        'BEGIN:VEVENT',
        'UID:event-2008-02-14@onegov.event',
        'SUMMARY:Squirrel Park Visit',
        'DTSTART;VALUE=DATE-TIME:20080214T091500Z',
        'DTEND;VALUE=DATE-TIME:20080214T150000Z',
        'DTSTAMP;VALUE=DATE-TIME:20080207T091500Z',
        'DESCRIPTION:<em>Furry</em> things will happen!',
        'CATEGORIES:fun,animals,furry',
        'LAST-MODIFIED;VALUE=DATE-TIME:20080207T091500Z',
        'LOCATION:Squirrel Park',
        'GEO:47.051752750515746;8.305739625357093',
        'URL:https://example.org/my-event',
        'END:VEVENT',
        'END:VCALENDAR'
    ])
