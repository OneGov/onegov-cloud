import pytest
from sedate import utcnow

from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import \
    NOTIFICATION_TYPES, CourseNotificationTemplate
from onegov.fsi.models.course_reservation import CourseReservation


def test_attendee_as_external(session, external_attendee):
    external, data = external_attendee(session)
    # Test the backrefs and how they work
    assert external.user_id is None
    assert external.user is None


def test_attendee_1(
        session, attendee, future_course_event, member, course_event):
    # past_event = course_event(session)
    course_event = future_course_event(session)
    attendee, data = attendee(session)
    member = member(session)
    assert attendee.reservations.count() == 0
    assert attendee.possible_course_events().count() == 1

    assert attendee.user == member
    assert member.attendee == attendee

    # Add a reservation
    reservation = CourseReservation(
        course_event_id=course_event[0].id, attendee_id=attendee.id)
    session.add(reservation)
    session.flush()
    assert attendee.reservations.count() == 1
    assert course_event[0].start > utcnow()
    assert attendee.course_events.first() == course_event[0]
    assert attendee.possible_course_events().count() == 0

    # Test reservation backref
    assert reservation.attendee == attendee

    # Check the event of the the reservation
    assert attendee.reservations[0].course_event == course_event[0]

    # delete the reservation
    attendee.reservations.remove(reservation)

    # and add it differently
    attendee.reservations.append(reservation)
    assert attendee.reservations.count() == 1


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
        CourseReservation(course_event_id=course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True),
        CourseReservation(course_event_id=future_course_event[0].id,
                    attendee_id=attendee[0].id, event_completed=True)))
    session.flush()

    future_course_event[0].mandatory_refresh = False
    assert attendee[0].repeating_courses.count() == 1


def test_course_event_1(session, course, course_event, attendee):
    attendee_, data = attendee(session)
    course, data = course(session)
    event, data = course_event(session)

    assert event.attendees.count() == 0
    assert event.reservations.count() == 0

    # Add a participant via a reservation
    placeholder = CourseReservation(
        dummy_desc='Placeholder', course_event_id=event.id)
    session.add_all((
        placeholder,
        CourseReservation(course_event_id=event.id, attendee_id=attendee_.id)
    ))
    session.flush()

    assert event.reservations.count() == 2
    assert event.attendees.count() == 1
    assert event.available_seats == 20 - 2
    assert event.possible_bookers().count() == 0
    attendee_2, data = attendee(session, first_name='2')
    assert event.possible_bookers().first() == attendee_2
    assert event.possible_bookers(external_only=True).count() == 0

    # Test course behind the event
    assert event.name == event.course.name
    assert event.description == event.course.description
    assert event.course == course

    assert course.events.all() == [event]


def test_reservation_1(session, attendee, course_event):
    attendee = attendee(session)
    course_event = course_event(session)
    res = CourseReservation(
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
    assert session.query(CourseReservation).count() == 2
    session.delete(event)
    assert session.query(CourseReservation).count() == 0


def test_cascading_attendee_deletion(session, db_mock_session):
    # If an attendee is deleted, his reservations should be deleted
    session = db_mock_session(session)
    attendee = session.query(CourseAttendee).first()
    assert session.query(CourseReservation).count() == 2
    session.delete(attendee)
    assert session.query(CourseReservation).count() == 1


def test_notification_templates(session, course_event, notification_template):
    event, data = course_event(session)
    templates = []
    for type_ in NOTIFICATION_TYPES:
        template, data = notification_template(
            session, type=type_, course_event_id=event.id)
        templates.append(template)

    for template in session.query(CourseNotificationTemplate):
        print(template.course_event_id)

    assert len(event.notification_templates) == 4
    assert templates[0].text == 'Hello World'
    assert event.info_template == templates[0]
    assert event.reservation_template == templates[1]
    assert event.reminder_template == templates[2]
    assert event.cancellation_template == templates[3]
