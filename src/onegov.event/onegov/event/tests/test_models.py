import pytest
import transaction

from datetime import datetime
from onegov.event import Event, Occurrence
from sedate import replace_timezone, to_timezone


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
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2008, 2, 7, 16, 00, timezone)
    event.title = 'Squirrel Park Visit'
    event.content = {'description': '<em>Furry</em> things will happen!'}
    event.location = 'Squirrel Park'
    event.tags = 'fun, animals, furry'
    event.meta = {'submitter': 'fat.pauly@squirrelpark.org'}
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
    assert occurence.event.location == event.location
    assert occurence.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags


def test_create_event_recurring(session):
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2008, 2, 7, 16, 0, timezone)
    event.title = 'Squirrel Park Visit'
    event.content = {'description': '<em>Furry</em> things will happen!'}
    event.location = 'Squirrel Park'
    event.tags = 'fun, animals, furry'
    event.meta = {'submitter': 'fat.pauly@squirrelpark.org'}
    event.recurrence = 'RRULE:FREQ=DAILY;INTERVAL=2;COUNT=5'
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 5
    assert occurrences[0].timezone == event.timezone
    assert occurrences[0].start == event.start
    assert occurrences[0].end == event.end
    assert occurrences[0].event.title == event.title
    assert occurrences[0].title == event.title
    assert occurrences[0].event.content == event.content
    assert occurrences[0].event.location == event.location
    assert occurrences[0].location == event.location
    assert occurrences[0].event.tags == event.tags
    assert occurrences[1].start == tzdatetime(2008, 2, 9, 10, 15, timezone)
    assert occurrences[1].end == tzdatetime(2008, 2, 9, 16, 00, timezone)
    assert occurrences[2].start == tzdatetime(2008, 2, 11, 10, 15, timezone)
    assert occurrences[2].end == tzdatetime(2008, 2, 11, 16, 00, timezone)
    assert occurrences[3].start == tzdatetime(2008, 2, 13, 10, 15, timezone)
    assert occurrences[3].end == tzdatetime(2008, 2, 13, 16, 00, timezone)
    assert occurrences[4].start == tzdatetime(2008, 2, 15, 10, 15, timezone)
    assert occurrences[4].end == tzdatetime(2008, 2, 15, 16, 00, timezone)


def test_create_event_recurring_dtstart(session):
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2008, 2, 7, 16, 00, timezone)
    event.title = 'Squirrel Park Visit'
    event.recurrence = ('DTSTART:19970902T090000\n'
                        'RRULE:FREQ=DAILY;INTERVAL=2;COUNT=5')
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 5
    assert occurrences[0].start == tzdatetime(1997, 9, 2, 9, 0, timezone)
    assert occurrences[0].end == tzdatetime(1997, 9, 2, 14, 45, timezone)
    assert occurrences[1].start == tzdatetime(1997, 9, 4, 9, 0, timezone)
    assert occurrences[1].end == tzdatetime(1997, 9, 4, 14, 45, timezone)
    assert occurrences[2].start == tzdatetime(1997, 9, 6, 9, 0, timezone)
    assert occurrences[2].end == tzdatetime(1997, 9, 6, 14, 45, timezone)
    assert occurrences[3].start == tzdatetime(1997, 9, 8, 9, 0, timezone)
    assert occurrences[3].end == tzdatetime(1997, 9, 8, 14, 45, timezone)
    assert occurrences[4].start == tzdatetime(1997, 9, 10, 9, 0, timezone)
    assert occurrences[4].end == tzdatetime(1997, 9, 10, 14, 45, timezone)


def test_create_event_recurring_limit(session):
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    year = datetime.today().year
    event.timezone = timezone
    event.start = tzdatetime(year, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(year, 2, 7, 16, 00, timezone)
    event.title = 'Squirrel Park Visit'
    event.recurrence = 'RRULE:FREQ=YEARLY;INTERVAL=1;COUNT=5'
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].start == event.start
    assert occurrences[0].end == event.end
    assert occurrences[1].start == tzdatetime(year+1, 2, 7, 10, 15, timezone)
    assert occurrences[1].end == tzdatetime(year+1, 2, 7, 16, 00, timezone)


def test_update_event(session):
    timezone = 'Europe/Zurich'

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2008, 2, 7, 16, 00, timezone)
    event.title = 'Squirrel Park Visit'
    event.content = {'description': '<em>Furry</em> things will happen!'}
    event.location = 'Squirrel Park'
    event.tags = 'fun, animals, furry'
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
    assert occurence.event.location == event.location
    assert occurence.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags

    event.start = tzdatetime(2009, 2, 7, 10, 15, timezone)
    event.end = tzdatetime(2009, 2, 7, 10, 15, timezone)
    event.title = 'Squirrel Park Visit - Cancelled'
    event.content = {'description': 'No <em>Furry</em> things will happen! :('}
    event.location = '-'
    event.tags = 'no fun, no animals'

    assert len(session.query(Event).one().occurrences) == 1
    occurence = session.query(Event).one().occurrences[0]
    assert occurence.timezone == event.timezone
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.title == event.title
    assert occurence.event.content == event.content
    assert occurence.event.location == event.location
    assert occurence.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags

    event.recurrence = 'RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2'
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

    event.recurrence = ''
    assert session.query(Occurrence).count() == 1
    assert len(session.query(Event).one().occurrences) == 1


def test_display_start_end(session):
    timezone = 'US/Eastern'
    start = tzdatetime(2008, 2, 7, 10, 15, timezone)
    end = tzdatetime(2008, 2, 7, 16, 00, timezone)

    event = Event(state='initiated')
    event.timezone = timezone
    event.start = start
    event.end = end
    event.title = 'Squirrel Park Visit'
    session.add(event)

    event.submit()
    event.publish()
    transaction.commit()

    event = session.query(Event).one()
    assert str(event.start.tzinfo) == 'UTC'
    assert str(event.end.tzinfo) == 'UTC'
    assert event.timezone == timezone
    assert event.display_start() == start
    assert event.display_start('UTC') == to_timezone(start, 'UTC')
    assert event.display_start('Europe/Zurich') == to_timezone(start,
                                                               'Europe/Zurich')
    assert len(event.occurrences) == 1

    occurrence = session.query(Occurrence).one()
    assert occurrence == event.occurrences[0]
    assert str(occurrence.start.tzinfo) == 'UTC'
    assert str(occurrence.end.tzinfo) == 'UTC'
    assert occurrence.timezone == timezone
    assert occurrence.display_start() == start
    assert occurrence.display_start('UTC') == to_timezone(start, 'UTC')
    assert occurrence.display_start('Europe/Zurich') == to_timezone(
        start, 'Europe/Zurich'
    )
    assert occurrence.display_end() == end
    assert occurrence.display_end('UTC') == to_timezone(end, 'UTC')
    assert occurrence.display_end('Europe/Zurich') == to_timezone(
        end, 'Europe/Zurich'
    )

    event.recurrence = 'RRULE:FREQ=DAILY;INTERVAL=2;COUNT=2'
    transaction.commit()

    event = session.query(Event).one()
    assert str(event.start.tzinfo) == 'UTC'
    assert str(event.end.tzinfo) == 'UTC'
    assert event.timezone == timezone
    assert event.display_start() == start
    assert event.display_start('UTC') == to_timezone(start, 'UTC')
    assert event.display_start('Europe/Zurich') == to_timezone(start,
                                                               'Europe/Zurich')
    assert len(event.occurrences) == 2

    occurrences = session.query(Occurrence).all()
    assert len(occurrences) == 2
    occurrence = occurrences[0]
    assert str(occurrence.start.tzinfo) == 'UTC'
    assert str(occurrence.end.tzinfo) == 'UTC'
    assert occurrence.timezone == timezone
    assert occurrence.display_start() == start
    assert occurrence.display_start('UTC') == to_timezone(start, 'UTC')
    assert occurrence.display_start('Europe/Zurich') == to_timezone(
        start, 'Europe/Zurich'
    )
    assert occurrence.display_end() == end
    assert occurrence.display_end('UTC') == to_timezone(end, 'UTC')
    assert occurrence.display_end('Europe/Zurich') == to_timezone(
        end, 'Europe/Zurich'
    )

    occurrence = occurrences[1]
    start = tzdatetime(2008, 2, 9, 10, 15, timezone)
    end = tzdatetime(2008, 2, 9, 16, 00, timezone)
    assert str(occurrence.start.tzinfo) == 'UTC'
    assert str(occurrence.end.tzinfo) == 'UTC'
    assert occurrence.timezone == timezone
    assert occurrence.display_start() == start
    assert occurrence.display_start('UTC') == to_timezone(start, 'UTC')
    assert occurrence.display_start('Europe/Zurich') == to_timezone(
        start, 'Europe/Zurich'
    )
    assert occurrence.display_end() == end
    assert occurrence.display_end('UTC') == to_timezone(end, 'UTC')
    assert occurrence.display_end('Europe/Zurich') == to_timezone(
        end, 'Europe/Zurich'
    )


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
