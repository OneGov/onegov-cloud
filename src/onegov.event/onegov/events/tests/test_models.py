import pytest

from datetime import datetime
from onegov.event import Event, Occurrence


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
    event = Event(state='initiated')
    event.start = datetime(2008, 2, 7, 10, 15)
    event.end = datetime(2008, 2, 7, 16, 00)
    event.title = "Squirrel Park Visit"
    event.description = "<em>Furry</em> things will happen!"
    event.location = "Squirrel Park"
    event.tags = "fun, animals, furry"
    session.add(event)

    event.submit()
    event.publish()

    occurence = session.query(Event).one().occurrences[0]
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.event.description == event.description
    assert occurence.event.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags


def test_create_event_recurring(session):
    event = Event(state='initiated')
    event.start = datetime(2008, 2, 7, 10, 15)
    event.end = datetime(2008, 2, 7, 16, 00)
    event.title = "Squirrel Park Visit"
    event.description = "<em>Furry</em> things will happen!"
    event.location = "Squirrel Park"
    event.tags = "fun, animals, furry"
    event.recurrence = "RRULE:FREQ=DAILY;INTERVAL=2;COUNT=5"
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 5
    assert occurrences[0].start == event.start
    assert occurrences[0].end == event.end
    assert occurrences[0].event.title == event.title
    assert occurrences[0].event.description == event.description
    assert occurrences[0].event.location == event.location
    assert occurrences[0].event.tags == event.tags
    assert occurrences[1].start == datetime(2008, 2, 9, 10, 15)
    assert occurrences[1].end == datetime(2008, 2, 9, 16, 00)
    assert occurrences[2].start == datetime(2008, 2, 11, 10, 15)
    assert occurrences[2].end == datetime(2008, 2, 11, 16, 00)
    assert occurrences[3].start == datetime(2008, 2, 13, 10, 15)
    assert occurrences[3].end == datetime(2008, 2, 13, 16, 00)
    assert occurrences[4].start == datetime(2008, 2, 15, 10, 15)
    assert occurrences[4].end == datetime(2008, 2, 15, 16, 00)


def test_create_event_recurring_dtstart(session):
    event = Event(state='initiated')
    event.start = datetime(2008, 2, 7, 10, 15)
    event.end = datetime(2008, 2, 7, 16, 00)
    event.title = "Squirrel Park Visit"
    event.recurrence = ("DTSTART:19970902T090000\n"
                        "RRULE:FREQ=DAILY;INTERVAL=2;COUNT=5")
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 5
    assert occurrences[0].start == datetime(1997, 9, 2, 9, 0)
    assert occurrences[0].end == datetime(1997, 9, 2, 14, 45)
    assert occurrences[1].start == datetime(1997, 9, 4, 9, 0)
    assert occurrences[1].end == datetime(1997, 9, 4, 14, 45)
    assert occurrences[2].start == datetime(1997, 9, 6, 9, 0)
    assert occurrences[2].end == datetime(1997, 9, 6, 14, 45)
    assert occurrences[3].start == datetime(1997, 9, 8, 9, 0)
    assert occurrences[3].end == datetime(1997, 9, 8, 14, 45)
    assert occurrences[4].start == datetime(1997, 9, 10, 9, 0)
    assert occurrences[4].end == datetime(1997, 9, 10, 14, 45)


def test_create_event_recurring_limit(session):
    event = Event(state='initiated')
    year = datetime.today().year
    event.start = datetime(year, 2, 7, 10, 15)
    event.end = datetime(year, 2, 7, 16, 00)
    event.title = "Squirrel Park Visit"
    event.recurrence = "RRULE:FREQ=YEARLY;INTERVAL=1;COUNT=5"
    session.add(event)

    event.submit()
    event.publish()

    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].start == event.start
    assert occurrences[0].end == event.end
    assert occurrences[1].start == datetime(year+1, 2, 7, 10, 15)
    assert occurrences[1].end == datetime(year+1, 2, 7, 16, 00)


def test_update_event(session):
    event = Event(state='initiated')
    event.start = datetime(2008, 2, 7, 10, 15)
    event.end = datetime(2008, 2, 7, 16, 00)
    event.title = "Squirrel Park Visit"
    event.description = "<em>Furry</em> things will happen!"
    event.location = "Squirrel Park"
    event.tags = "fun, animals, furry"
    session.add(event)

    event.submit()
    event.publish()

    occurence = session.query(Event).one().occurrences[0]
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.event.description == event.description
    assert occurence.event.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags

    event.start = datetime(2009, 2, 7, 10, 15)
    event.end = datetime(2009, 2, 7, 10, 15)
    event.title = "Squirrel Park Visit - Cancelled"
    event.description = "No <em>Furry</em> things will happen! :("
    event.location = "-"
    event.tags = "no fun, no animals"

    assert len(session.query(Event).one().occurrences) == 1
    occurence = session.query(Event).one().occurrences[0]
    assert occurence.start == event.start
    assert occurence.end == event.end
    assert occurence.event.title == event.title
    assert occurence.event.description == event.description
    assert occurence.event.location == event.location
    assert occurence.event.tags == event.tags
    assert occurence.tags == event.tags

    event.recurrence = "RRULE:FREQ=DAILY;INTERVAL=1;COUNT=2"
    occurrences = session.query(Event).one().occurrences
    assert len(occurrences) == 2
    assert occurrences[0].start == datetime(2009, 2, 7, 10, 15)
    assert occurrences[0].end == datetime(2009, 2, 7, 10, 15)
    assert occurrences[1].start == datetime(2009, 2, 8, 10, 15)
    assert occurrences[1].end == datetime(2009, 2, 8, 10, 15)

    event.recurrence = ""
    assert session.query(Occurrence).count() == 1
    assert len(session.query(Event).one().occurrences) == 1


def test_delete_event(session):
    event = Event(start=datetime(2008, 2, 7, 10, 15), state='initiated',
                  end=datetime(2008, 2, 7, 16, 00), title='event')
    session.add(event)
    session.delete(session.query(Event).one())
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(start=datetime(2008, 2, 7, 10, 15), state='initiated',
                  end=datetime(2008, 2, 7, 16, 00), title='event')
    session.add(event)
    event.submit()
    session.delete(session.query(Event).one())
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(start=datetime(2008, 2, 7, 10, 15), state='initiated',
                  end=datetime(2008, 2, 7, 16, 00), title='event')
    session.add(event)
    event.submit()
    event.publish()
    session.delete(session.query(Event).one())
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0

    event = Event(start=datetime(2008, 2, 7, 10, 15), state='initiated',
                  end=datetime(2008, 2, 7, 16, 00), title='event')
    session.add(event)
    event.submit()
    event.publish()
    event.withdraw()
    session.delete(session.query(Event).one())
    assert session.query(Event).count() == 0
    assert session.query(Occurrence).count() == 0
