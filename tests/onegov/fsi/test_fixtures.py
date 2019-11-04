from onegov.fsi.models.course import Course
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.reservation import Reservation


def test_db_mock_function_session(session, db_mock_session):
    session = db_mock_session(session)

    assert session.query(CourseAttendee).first()
    assert session.query(Course).first()
    assert session.query(CourseEvent).first()
    assert session.query(Reservation).count() == 2


def test_db_mock_app_session(fsi_app, db_mock_session):
    session = fsi_app.session()
    session = db_mock_session(session)

    assert session.query(CourseAttendee).first()
    assert session.query(Course).first()
    assert session.query(CourseEvent).first()
    assert session.query(Reservation).count() == 2
