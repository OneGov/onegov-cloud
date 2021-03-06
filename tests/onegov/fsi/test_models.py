import datetime
from sedate import utcnow

from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import get_template_default
from onegov.fsi.models.course_subscription import CourseSubscription


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
    assert attendee.subscriptions.count() == 0
    assert attendee.possible_course_events().count() == 1

    assert attendee.user == member
    assert member.attendee == attendee

    # Add a subscription
    subscription = CourseSubscription(
        course_event_id=course_event[0].id, attendee_id=attendee.id)
    session.add(subscription)
    session.flush()
    assert attendee.subscriptions.count() == 1
    assert course_event[0].start > utcnow()
    assert attendee.course_events.first() == course_event[0]
    assert attendee.possible_course_events().count() == 0

    # Test subscription backref
    assert subscription.attendee == attendee

    # Check the event of the the subscription
    assert attendee.subscriptions[0].course_event == course_event[0]

    # delete the subscription
    attendee.subscriptions.remove(subscription)

    # and add it differently
    attendee.subscriptions.append(subscription)
    assert attendee.subscriptions.count() == 1


def test_course_event_1(session, course, course_event, attendee):
    attendee_, data = attendee(session)
    course, data = course(session)
    event, data = course_event(session)
    delta = datetime.timedelta(days=265)

    assert event.attendees.count() == 0
    assert event.subscriptions.count() == 0

    # Add a participant via a subscription
    placeholder = CourseSubscription(
        dummy_desc='Placeholder', course_event_id=event.id)
    session.add_all((
        placeholder,
        CourseSubscription(course_event_id=event.id, attendee_id=attendee_.id)
    ))
    session.flush()

    assert event.subscriptions.count() == 2
    assert event.attendees.count() == 1
    assert event.available_seats == 20 - 2
    assert event.possible_subscribers().first() is None

    # Test possible and excluded subscribers
    attendee_2, data = attendee(session, first_name='2')
    assert event.possible_subscribers().first() == attendee_2
    assert event.possible_subscribers(external_only=True).count() == 0

    event2, data = course_event(
        session, start=event.start + delta, end=event.end + delta)

    assert event2.excluded_subscribers(as_uids=False).all() == []
    # assert event2.possible_subscribers().first() == attendee_2

    # Add attendee2 also to event, so that can not book event2
    year = event.start.year
    assert year == event2.start.year
    assert event2.subscriptions.first() is None
    session.add(
        CourseSubscription(
            attendee_id=attendee_2.id,
            course_event_id=event.id
        )
    )
    session.flush()

    # Subscription in for event2 has impact on possible bookers in event
    other_subscribers = event.attendees.all()
    assert event2.excluded_subscribers(
        as_uids=False, year=year).all() == other_subscribers
    assert event2.can_book(attendee_, year=year) is False

    assert attendee_ in event.attendees.all()
    assert event.can_book(attendee_, year=year) is False

    # Test course behind the event
    assert event.name == event.course.name
    assert event.description == event.course.description
    assert event.course == course

    assert course.events.all() == [event, event2]
    assert course.future_events.all() == []


def test_reservation_1(session, attendee, course_event):
    attendee = attendee(session)
    course_event = course_event(session)
    res = CourseSubscription(
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
    # If a course event is deleted, all the subscriptions should be deleted
    session = db_mock_session(session)
    event = session.query(CourseEvent).first()
    assert event.subscriptions.count() == 2
    session.delete(event)
    assert session.query(CourseSubscription).count() == 0
    assert event.subscriptions.count() == 0


def test_cascading_attendee_deletion(session, db_mock_session):
    # If an attendee is deleted, his reservations should be deleted
    session = db_mock_session(session)
    attendee = session.query(CourseAttendee).first()
    assert session.query(CourseSubscription).count() == 2
    session.delete(attendee)
    assert session.query(CourseSubscription).count() == 1


def test_notification_templates_1(session, course_event):
    event, data = course_event(session)
    assert len(event.notification_templates) == 4
    assert event.info_template
    assert event.reservation_template
    assert event.reminder_template
    assert event.cancellation_template

    func = get_template_default
    assert event.info_template.subject == func(None, 'info')
    assert event.reservation_template.subject == func(None, 'reservation')
    assert event.reminder_template.subject == func(None, 'reminder')
    assert event.cancellation_template.subject == func(None, 'cancellation')
