import datetime

from sedate import utcnow

from onegov.fsi.models.course import Course
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


def test_course_1(session, course, attendee, mock_data_course_event):
    course, data = course
    mock = mock_data_course_event
    assert course.events.count() == 0

    # Add an event
    now = utcnow()
    tmr = now + datetime.timedelta(days=1)
    just_before = now - datetime.timedelta(minutes=2)

    event = CourseEvent(**mock(),
                        start=just_before, end=now, course_id=course.id)
    event_now = CourseEvent(**mock(), start=now, end=tmr, course_id=course.id)
    event_tmr = CourseEvent(**mock(), start=tmr, end=tmr, course_id=course.id)

    course.events.append(event)
    course.events.append(event_now)
    course.events.append(event_tmr)

    assert course.events.count() == 3
    assert session.query(CourseEvent).count() == 3

    # Test upcoming events
    assert course.next_event() == event_tmr
    assert course.upcoming_events == [event_now, event_tmr]


def test_reservation_as_placeholder():
    assert Reservation.as_placeholder('Test').attendee_id is None


def test_attendee_as_external(external_attendee):
    external, data = external_attendee
    # Test the backrefs and how they work
    assert external.user_id is None
    assert external.user is None


def test_attendee_1(session, attendee, course_event, member):
    attendee, data = attendee
    assert attendee.reservations.count() == 0

    assert attendee.user == member
    assert member.attendee == attendee

    # Add a reservation
    reservation = Reservation(
        course_event_id=course_event[0].id, attendee_id=attendee.id)
    session.add(reservation)
    session.flush()
    assert attendee.reservations.count() == 1
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


def test_attendee_upcoming_courses(
        session, attendee, course, course_event, future_course_event):

    # Add two reservations
    assert course[0].mandatory_refresh is True
    session.add_all((
        Reservation(course_event_id=course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True),
        Reservation(course_event_id=future_course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True)))
    session.flush()

    # Test for ignoring the date when future event is marked as completed
    assert attendee[0].upcoming_courses().count() == 2

    course[0].mandatory_refresh = False
    session.flush()
    assert not attendee[0].upcoming_courses().count() == 1


def test_course_event_1(session, course_event, course, attendee):
    event, data = course_event

    assert event.attendees.count() == 0
    assert event.reservations.count() == 0
    assert event.course == course[0]

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


def test_reservation(session, attendee, course_event):
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


def test_cascading_course_deletion(db_mock_session):
    # When a course is deleted, all course events should be deleted as well
    session = db_mock_session
    course = session.query(Course).one()
    session.delete(course)
    session.flush()
    assert session.query(CourseEvent).count() == 0
    assert session.query(Reservation).count() == 0


def test_cascading_event_deletion(db_mock_session, course_event):
    # If a course event is deleted, all the reservations should be deleted
    session = db_mock_session
    assert session.query(Reservation).count() == 2
    session.delete(course_event[0])
    session.flush()
    assert session.query(Reservation).count() == 0


def test_cascading_attendee_deletion(db_mock_session, attendee):
    # If an attendee is deleted, his reservations should be deleted
    session = db_mock_session
    assert session.query(Reservation).count() == 2
    session.delete(attendee[0])
    session.flush()
    assert session.query(Reservation).count() == 1


def test_notification_templates(session, notification_template):
    assert notification_template.text == 'Hello World'
