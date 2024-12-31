import datetime

from freezegun import freeze_time
from sedate import utcnow

from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import get_template_default
from onegov.fsi.models.course_subscription import CourseSubscription


def test_attendee(
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


def test_course_event(scenario):
    # if current date is last or second last day of the year, then freeze to
    # 28th of december
    if utcnow().date().month == 12 and utcnow().date().day in (30, 31):
        freeze_date = '2024-12-28'
    else:
        freeze_date = utcnow().date()

    with freeze_time(freeze_date):
        scenario.add_attendee()
        scenario.add_course(name='Course')
        scenario.add_course_event(scenario.latest_course, max_attendees=20)
        delta = datetime.timedelta(days=366)

        # Add a participant via a subscription
        event = scenario.latest_event
        scenario.add_subscription(event, None, dummy_desc='Placeholder')
        scenario.add_subscription(event, scenario.latest_attendee)

        # Add inactive attendee
        scenario.add_attendee(active=False)
        scenario.add_subscription(event, scenario.latest_attendee)

        scenario.commit()
        scenario.refresh()

        event = scenario.latest_event
        assert event.subscriptions.count() == 3
        assert event.attendees.count() == 2
        assert event.available_seats == 20 - 3
        assert event.possible_subscribers().first() is None

        # Test possible and excluded subscribers
        scenario.add_attendee(username='2@example.org')
        attendee_2 = scenario.latest_attendee

        # event = scenario.latest_event
        assert event.course
        assert event.possible_subscribers(year=event.end.year).all() == [
            attendee_2
        ]

        scenario.add_course_event(
            scenario.latest_course,
            start=event.start + delta, end=event.end + delta,
            max_attendees=20
        )
        event2 = scenario.latest_event

        # Event for a year later, exclude the one who has a subscription to
        # this course
        assert event.possible_subscribers(
            year=event.end.year + 1).count() == 1
        assert event2.possible_subscribers(
            year=event.end.year).count() == 1
        assert event2.possible_subscribers(
            year=event.end.year + 1).count() == 2
        assert event.possible_subscribers(external_only=True).count() == 0
        assert event.excluded_subscribers().count() == 2
        assert event2.possible_subscribers().first() == attendee_2

        assert scenario.latest_course.future_events.count() == 2


def test_subscription(session, attendee, course_event):
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


def test_notification_templates(session, course_event):
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
