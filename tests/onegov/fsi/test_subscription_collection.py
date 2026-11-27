from __future__ import annotations

from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.subscription import SubscriptionsCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.fsi.conftest import FsiScenario


def test_subscriptions_collection_properties(scenario: FsiScenario) -> None:
    scenario.add_attendee(role='member')
    att = scenario.latest_attendee
    scenario.add_course()
    scenario.add_course_event(course=scenario.latest_course)
    event = scenario.latest_event
    sub = scenario.add_subscription(event, att)
    scenario.commit()

    session = scenario.session
    auth: Any = att

    coll = SubscriptionsCollection(
        session, attendee_id=att.id, course_event_id=event.id,
        auth_attendee=auth)

    # __eq__
    assert coll == SubscriptionsCollection(
        session, attendee_id=att.id, course_event_id=event.id,
        auth_attendee=auth)
    assert coll != SubscriptionsCollection(session)
    assert coll != object()

    # course_event / attendee lookups
    assert coll.course_event is not None
    assert coll.course_event.id == event.id
    assert coll.attendee is not None
    assert coll.attendee.id == att.id
    assert SubscriptionsCollection(session).course_event is None
    assert SubscriptionsCollection(session).attendee is None

    # attendee_collection
    assert isinstance(coll.attendee_collection, CourseAttendeeCollection)

    # for_himself compares auth_attendee against attendee_id
    assert coll.for_himself is True
    assert SubscriptionsCollection(
        session, attendee_id=att.id).for_himself is False

    # by_id bypasses the filters
    found = coll.by_id(sub.id)
    assert found is not None
    assert found.id == sub.id

    # paging
    assert coll.page_index == 0
    other = coll.page_by_index(2)
    assert other.page == 2
    assert other.attendee_id == att.id
    assert other.course_event_id == event.id
