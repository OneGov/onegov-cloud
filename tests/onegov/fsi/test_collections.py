import datetime
from sedate import utcnow

from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.reservation import ReservationCollection

from onegov.fsi.models.course_event import CourseEvent
from tests.onegov.fsi.common import collection_attr_eq_test


def test_course_event_collection(session, course):
    now = utcnow()
    new_course_events = (
        CourseEvent(
            course_id=course(session)[0].id,
            location=f'Address, Room {i}',
            start=now + datetime.timedelta(days=i),
            end=now + datetime.timedelta(days=i, hours=2),
            presenter_name=f'P{i}',
            presenter_company=f'C{i}',
            presenter_email=f'{i}@email.com'
        ) for i in (-1, 1, 2)
    )
    session.add_all(new_course_events)
    session.flush()

    event_coll = CourseEventCollection(session)
    collection_attr_eq_test(event_coll, event_coll.page_by_index(1))
    result = event_coll.query()

    # Should return all events by default
    assert result.count() == 3

    # Test ordering and timestamp mixin
    assert result[0].created > result[1].created

    # Test upcoming only
    event_coll = CourseEventCollection(session, upcoming_only=True)
    assert event_coll.query().count() == 2

    # Test latest
    event_coll = CourseEventCollection.latest(session)
    assert event_coll.query().count() == 2

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
    # event_coll.add_placeholder('Placeholder', course_event)
    # Tests the secondary join event.attendees as well
    assert course_event.attendees.count() == 0
    # assert course_event.reservations.count() == 1


def test_attendee_collection(session, attendee):
    attendee, data = attendee(session)
    collection = CourseAttendeeCollection(session)
    collection_attr_eq_test(collection, collection.page_by_index(1))

    assert collection.query().one() == attendee

    # Exlude placeholders and return real users
    collection = CourseAttendeeCollection(session, exclude_external=True)
    assert collection.query().count() == 1


def test_reservation_collection_1(session, future_course_reservation):
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


def test_reservation_collection_query(
        session, attendee, planner, planner_editor, course_event,
        future_course_reservation, external_attendee):

    admin, data = planner(session)
    editor, data = planner_editor(session)
    att, data = attendee(session)
    external, data = external_attendee(session)
    event, data = course_event(session)
    future_course_reservation(
        session, course_event_id=event.id, attendee_id=att.id)
    future_course_reservation(session, attendee_id=editor.id)

    future_course_reservation(
        session, course_event_id=event.id, attendee_id=external.id)

    # unfiltered
    coll = ReservationCollection(session)
    assert coll.query().count() == 3

    # filter attendee
    coll.attendee_id = att.id
    assert coll.query().count() == 1

    coll.external_only = True
    assert coll.query().count() == 1

    coll.external_only = False
    coll.attendee_id = None

    # auth attendee is passed in path.py always
    coll.user_role = 'admin'
    coll.permissions = admin.permissions
    assert coll.query().count() == 3

    coll.user_role = 'editor'
    coll.permissions = editor.permissions
    assert coll.query().count() == 0

    # See the ones with permission without the external reservations
    att.organisation = 'A'
    coll.permissions = ['A']
    assert coll.query().count() == 1

    # member user_role
    coll.user_role = 'member'
    # coll.attendee_id will be set in path like
    coll.attendee_id = att.id
    assert coll.query().count() == 1
