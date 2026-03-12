from __future__ import annotations

import datetime

from freezegun import freeze_time
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_notification_template import get_template_default
from onegov.fsi.models.course_subscription import CourseSubscription
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.user import User
    from sqlalchemy.orm import Session
    from .conftest import Factory, FsiScenario


def test_attendee(
    session: Session,
    attendee: Factory[CourseAttendee],
    future_course_event: Factory[CourseEvent],
    member: Callable[[Session], User],
    course_event: Factory[CourseEvent]
) -> None:
    # past_event = course_event(session)
    course_event_, _ = future_course_event(session)
    attendee_, data = attendee(session)
    member_ = member(session)
    assert attendee_.subscriptions.count() == 0
    assert attendee_.possible_course_events().count() == 1

    assert attendee_.user == member_
    assert member_.attendee == attendee_  # type: ignore[attr-defined]

    # Add a subscription
    subscription = CourseSubscription(
        course_event_id=course_event_.id, attendee_id=attendee_.id)
    session.add(subscription)
    session.flush()
    assert attendee_.subscriptions.count() == 1
    assert course_event_.start > utcnow()
    assert attendee_.course_events.first() == course_event_
    assert attendee_.possible_course_events().count() == 0

    # Test subscription backref
    assert subscription.attendee == attendee_

    # Check the event of the the subscription
    assert attendee_.subscriptions[0].course_event == course_event_  # type: ignore[union-attr]

    # delete the subscription
    attendee_.subscriptions.remove(subscription)

    # and add it differently
    attendee_.subscriptions.append(subscription)
    assert attendee_.subscriptions.count() == 1


def test_course_event(scenario: FsiScenario) -> None:
    # if current date is last or second last day of the year, then freeze to
    # 28th of december
    freeze_date: str | datetime.date
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


def test_subscription(
    session: Session,
    attendee: Factory[CourseAttendee],
    course_event: Factory[CourseEvent]
) -> None:
    attendee_, _ = attendee(session)
    course_event_, _ = course_event(session)
    res = CourseSubscription(
        course_event_id=course_event_.id,
        attendee_id=attendee_.id
    )
    session.add(res)
    session.flush()

    # Test backrefs
    assert res.course_event == course_event_
    assert res.attendee == attendee_
    assert str(res) == 'L, F'


def test_cascading_event_deletion(
    session: Session,
    db_mock_session: Callable[[Session], Session]
) -> None:
    # If a course event is deleted, all the subscriptions should be deleted
    session = db_mock_session(session)
    event = session.query(CourseEvent).first()
    assert event is not None
    assert event.subscriptions.count() == 2
    session.delete(event)
    assert session.query(CourseSubscription).count() == 0
    assert event.subscriptions.count() == 0


def test_cascading_attendee_deletion(
    session: Session,
    db_mock_session: Callable[[Session], Session]
) -> None:
    # If an attendee is deleted, his reservations should be deleted
    session = db_mock_session(session)
    attendee = session.query(CourseAttendee).first()
    assert session.query(CourseSubscription).count() == 2
    session.delete(attendee)
    assert session.query(CourseSubscription).count() == 1


def test_notification_templates(
    session: Session,
    course_event: Factory[CourseEvent]
) -> None:
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
