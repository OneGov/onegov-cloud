from onegov.fsi.models.reservation import Reservation


def test_course(course, attendee):
    course, data = course
    for key, val in data.items():
        assert getattr(course, key) == val

    assert course.reservations == []

    # Add a reservation
    reservation = Reservation(course_id=course.id, attendee_id=attendee[0].id)
    course.reservations.append(reservation)
    assert len(course.reservations) == 1


def test_attendee(attendee, course):
    course, data = course
    attendee, data = attendee
    for key, val in data.items():
        assert getattr(attendee, key) == val
    assert attendee.reservations == []

    # Add a reservation
    reservation = Reservation(course_id=course.id, attendee_id=attendee.id)
    attendee.reservations.append(reservation)
    assert len(attendee.reservations) == 1

    # Test reservation backref
    assert reservation.attendee == attendee


def test_course_event(course_event):
    event, data = course_event
    for key, val in data.items():
        assert getattr(event, key) == val


