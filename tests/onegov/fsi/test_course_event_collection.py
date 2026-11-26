from __future__ import annotations

from datetime import timedelta
from onegov.fsi.collections.course_event import (
    CourseEventCollection,
    PastCourseEventCollection,
)
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.fsi.conftest import FsiScenario


def _setup(scenario: FsiScenario) -> None:
    scenario.add_course()
    course = scenario.latest_course
    scenario.add_course_event(
        course=course, start=utcnow() - timedelta(days=2), status='confirmed')
    scenario.add_course_event(
        course=course, start=utcnow() + timedelta(days=2), status='confirmed')
    scenario.commit()


def test_course_event_collection_course_property(
    scenario: FsiScenario
) -> None:
    _setup(scenario)
    course = scenario.latest_course
    session = scenario.session

    coll = CourseEventCollection(session, course_id=course.id)
    assert coll.course is not None
    assert coll.course.id == course.id
    assert CourseEventCollection(session).course is None


def test_course_event_collection_time_filters(scenario: FsiScenario) -> None:
    _setup(scenario)
    session = scenario.session

    assert CourseEventCollection(
        session, upcoming_only=True).query().count() == 1
    assert CourseEventCollection(
        session, past_only=True).query().count() == 1

    from_date = utcnow()
    assert CourseEventCollection(
        session, from_date=from_date).query().count() == 1

    assert CourseEventCollection(session, limit=1).query().count() == 1

    # next_event / past reminder queries are callable
    assert CourseEventCollection(session).next_event().count() == 1
    assert CourseEventCollection(
        session).get_past_reminder_date().count() == 2


def test_course_event_collection_equality_and_latest(
    scenario: FsiScenario
) -> None:
    session = scenario.session
    assert CourseEventCollection(session) == CourseEventCollection(session)
    assert CourseEventCollection(session) != CourseEventCollection(
        session, past_only=True)
    assert CourseEventCollection(session) != object()

    latest = CourseEventCollection.latest(session, limit=3)
    assert latest.upcoming_only is True
    assert latest.limit == 3

    other = CourseEventCollection(session, course_id=None).page_by_index(2)
    assert other.page == 2


def test_past_course_event_collection(scenario: FsiScenario) -> None:
    _setup(scenario)
    session = scenario.session

    past = PastCourseEventCollection(session)
    assert past.past_only is True
    assert past.sort_desc is True
    # only confirmed past events
    assert past.query().count() == 1

    other = past.page_by_index(1)
    assert other.page == 1
    assert other.past_only is True
