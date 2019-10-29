import datetime

from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


def test_course_1(session, course, attendee):
    course, data = course
    for key, val in data.items():
        assert getattr(course, key) == val

    assert course.events == []

    # Add an event
    today = datetime.datetime.today()
    event = CourseEvent(
        course_id=course.id,
        name='N',
        start=today,
        end=today + datetime.timedelta(hours=2),
        presenter_name='P',
        presenter_company='C'
    )
    course.events.append(event)
    assert len(course.events) == 1
    assert session.query(CourseEvent).one()


def test_attendee(attendee, course):
    course, data = course
    attendee, data = attendee
    for key, val in data.items():
        assert getattr(attendee, key) == val
    assert attendee.reservations == []

    # Add a reservation
    reservation = Reservation(
        course_event_id=course.id, attendee_id=attendee.id)
    attendee.reservations.append(reservation)
    assert len(attendee.reservations) == 1

    # Test reservation backref
    assert reservation.attendee == attendee

    # Test backref to course event
    assert attendee.course_events == []


def test_course_event(session, course_event, placeholder):
    event, data = course_event
    for key, val in data.items():
        assert getattr(event, key) == val
    assert event.attendees.all() == []

    # # Add a participant via a reservation
    # reservation = Reservation(
    #     course_event_id=event.id, attendee_id=placeholder[0].id)
    # session.add(reservation)
    # session.flush()
    # assert len(event.attendees) == 1



