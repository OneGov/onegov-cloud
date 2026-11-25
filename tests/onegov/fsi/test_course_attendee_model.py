from __future__ import annotations

from datetime import timedelta
from onegov.fsi.models.course_attendee import CourseAttendee
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.fsi.conftest import FsiScenario


def test_course_attendee_str() -> None:
    assert str(CourseAttendee(first_name='Anna', last_name='Alpha')) == \
        'Alpha, Anna'
    assert str(CourseAttendee(_email='user@example.org')) == \
        'user@example.org'
    assert str(CourseAttendee()) == 'NO NAME NO EMAIL'


def test_course_attendee_event_queries(scenario: FsiScenario) -> None:
    scenario.add_attendee(role='member')
    attendee = scenario.latest_attendee
    scenario.add_course()
    course = scenario.latest_course

    # an upcoming, not-yet-completed confirmed event
    scenario.add_course_event(
        course=course, start=utcnow() + timedelta(days=2), status='confirmed')
    scenario.add_subscription(
        scenario.latest_event, attendee, event_completed=False)

    # a separate completed event
    scenario.add_course_event(
        course=course, start=utcnow() + timedelta(days=4), status='confirmed')
    scenario.add_subscription(
        scenario.latest_event, attendee, event_completed=True)
    scenario.commit()

    att = scenario.session.query(CourseAttendee).filter_by(
        id=attendee.id).one()
    # only the upcoming, not-completed, confirmed event
    assert att.confirmed_course_events.count() == 1
    # only the completed subscription
    assert att.total_done_course_events.count() == 1
