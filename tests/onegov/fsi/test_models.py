from onegov.fsi.models.reserveration import Reservation


def test_course(session, course, attendee):
    course, data = course
    for key, val in data.items():
        assert getattr(course, key) == val

    assert course.reservations == []

    # Add a reservation
    reservation = Reservation(course_id=course.id, attendee_id=attendee[0].id)
    course.reservations.append(reservation)
    assert len(course.reservations) == 1
    assert session.query(Reservation).one()


def test_attendee(attendee):
    attendee, data = attendee
    for key, val in data.items():
        assert getattr(attendee, key) == val


def test_course_event(course_event):
    event, data = course_event
    for key, val in data.items():
        assert getattr(event, key) == val


