import datetime

import pytest
from sedate import utcnow

from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


def test_reservation_as_placeholder():
    assert Reservation.as_placeholder('Test').attendee_id is None


def test_attendee_as_external(session, external_attendee):
    external, data = external_attendee(session)
    # Test the backrefs and how they work
    assert external.user_id is None
    assert external.user is None


def test_attendee_1(session, attendee, future_course_event, member):
    course_event = future_course_event
    attendee, data = attendee(session)
    course_event = course_event(session)
    member = member(session)
    assert attendee.reservations.count() == 0

    assert attendee.user == member
    assert member.attendee == attendee

    # Add a reservation
    reservation = Reservation(
        course_event_id=course_event[0].id, attendee_id=attendee.id)
    session.add(reservation)
    session.flush()
    assert attendee.reservations.count() == 1
    assert course_event[0].start > utcnow()
    assert attendee.course_events.first() == course_event[0]

    # Test reservation backref
    assert reservation.attendee == attendee

    # Check the event of the the reservation
    assert attendee.reservations[0].course_event == course_event[0]

    # delete the reservation
    attendee.reservations.remove(reservation)

    # and add it differently
    attendee.reservations.append(reservation)
    assert attendee.reservations.count() == 1

    # Test templates backref
    assert attendee.templates == []


@pytest.mark.skip('Wait until model definitions are clear')
def test_attendee_upcoming_courses(
        session, attendee, course_event, future_course_event):

    attendee = attendee(session)
    course_event = course_event(session)
    future_course_event = future_course_event(session)

    # Add two reservations
    assert course_event[0].mandatory_refresh is True
    assert future_course_event[0].mandatory_refresh is True
    session.add_all((
        Reservation(course_event_id=course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True),
        Reservation(course_event_id=future_course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True)))
    session.flush()

    future_course_event[0].mandatory_refresh = False
    assert attendee[0].repeating_courses.count() == 1


def test_course_event_1(session, course_event, attendee):
    attendee = attendee(session)
    event, data = course_event(session)

    assert event.attendees.count() == 0
    assert event.reservations.count() == 0

    # Add a participant via a reservation
    placeholder = Reservation.as_placeholder(
        'Placeholder', course_event_id=event.id)
    session.add_all((
        placeholder,
        Reservation(course_event_id=event.id, attendee_id=attendee[0].id)
    ))
    session.flush()

    assert event.reservations.count() == 2
    assert event.attendees.count() == 1
    assert event.available_seats == 20 - 2

    # Test cancel reservation
    event.cancel_reservation(placeholder)
    assert event.reservations.count() == 1


def test_reservation_1(session, attendee, course_event):
    attendee = attendee(session)
    course_event = course_event(session)
    res = Reservation(
        course_event_id=course_event[0].id,
        attendee_id=attendee[0].id
    )
    session.add(res)
    session.flush()

    # Test backrefs
    assert res.course_event == course_event[0]
    assert res.attendee == attendee[0]
    assert str(res) == 'L, F'


def test_cascading_event_deletion(session, db_mock_session):
    # If a course event is deleted, all the reservations should be deleted
    session = db_mock_session(session)
    event = session.query(CourseEvent).first()
    assert session.query(Reservation).count() == 2
    session.delete(event)
    assert session.query(Reservation).count() == 0


def test_cascading_attendee_deletion(session, db_mock_session):
    # If an attendee is deleted, his reservations should be deleted
    session = db_mock_session(session)
    attendee = session.query(CourseAttendee).first()
    assert session.query(Reservation).count() == 2
    session.delete(attendee)
    assert session.query(Reservation).count() == 1


def test_notification_templates(session, notification_template):
    template, data = notification_template(session)
    event = session.query(CourseEvent).first()
    assert template.text == 'Hello World'
    assert not isinstance(event.template, list)
    assert event.template == template
