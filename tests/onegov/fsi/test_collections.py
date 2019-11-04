import datetime
from uuid import uuid4

import pytest
from sedate import utcnow

from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.course import Course
from mixer.backend.sqlalchemy import mixer

from onegov.fsi.models.course_event import CourseEvent
from tests.onegov.fsi.common import collection_attr_eq_test


def test_course_collection(session):
    new_courses = (
        mixer.blend(
            Course,
            refresh_interval=datetime.timedelta(days=20)
        ) for i in range(11)
    )

    collection = CourseCollection(session)
    session.add_all(new_courses)
    session.flush()

    # Test pagination
    assert len(collection.batch) == 10
    assert collection.page_index == 0
    assert collection.pages_count == 2

    result = collection.query()
    assert result.count() == 11

    next_ = collection.next
    assert next_.page_index != collection.page_index
    by_index = collection.page_by_index(2)

    collection_attr_eq_test(collection, by_index)

    # assert descending order
    assert result[0].created > result[1].created


def test_course_event_collection(session, course):
    course, data = course(session)
    now = utcnow()
    new_course_events = (
        mixer.blend(
            CourseEvent,
            start=now + datetime.timedelta(days=i),
            end=now + datetime.timedelta(days=i, hours=2),
            course_id=course.id

        ) for i in (-1, 1, 2)
    )
    session.add_all(new_course_events)
    session.flush()

    event_coll = CourseEventCollection(session)
    collection_attr_eq_test(event_coll, event_coll.page_by_index(1))
    result = event_coll.query()

    # Should return upcoming events by default
    assert result.count() == 2

    # Test ordering and timestamp mixin
    assert result[0].created > result[1].created

    # Test all results
    event_coll = CourseEventCollection(session, upcoming_only=False)
    assert event_coll.query().count() == 3

    # Test filtering with wrong course id
    event_coll = CourseEventCollection(session, course_id=uuid4())
    assert event_coll.query().count() == 0

    # Test all past events
    event_coll = CourseEventCollection(session, past_only=True)
    assert event_coll.query().count() == 1

    # Test from specific date
    tmr = now + datetime.timedelta(days=1)
    event_coll = CourseEventCollection(session, from_date=tmr)
    assert event_coll.query().count() == 1


def test_event_collection_add_placeholder(session, course_event):
    # Test add_placeholder method
    course_event, data = course_event(session)
    event_coll = CourseEventCollection(session)
    event_coll.add_placeholder('Placeholder', course_event)
    # Tests the secondary join event.attendees as well
    assert course_event.attendees.count() == 0
    assert course_event.reservations.count() == 1


def test_attendee_collection(session, attendee):
    attendee, data = attendee(session)
    collection = CourseAttendeeCollection(session)
    collection_attr_eq_test(collection, collection.page_by_index(1))

    assert collection.query().one() == attendee

    # Exlude placeholders and return real users
    collection = CourseAttendeeCollection(session, exclude_external=True)
    assert collection.query().count() == 1


def test_reservation_collection(session, future_course_reservation):
    future_course_reservation(session)
    soon = utcnow() + datetime.timedelta(seconds=60)
    reservations = ReservationCollection(session)
    res = reservations.for_reminder_mails().first()
    assert res
    course_event = res.course_event
    assert course_event.start - course_event.schedule_reminder_before < soon

    # Change the reminder before value
    course_event.schedule_reminder_before = datetime.timedelta(days=4)
    session.flush()

    assert course_event.start - course_event.schedule_reminder_before > soon
    assert reservations.for_reminder_mails().count() == 0
