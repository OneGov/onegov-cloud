from __future__ import annotations

from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection,
)
from onegov.fsi.utils import handle_empty_p_tags


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.fsi.conftest import FsiScenario


def test_handle_empty_p_tags() -> None:
    assert handle_empty_p_tags('<p></p>') == ''
    assert handle_empty_p_tags('<p>text</p>') == '<p>text</p>'


def test_notification_template_collection(scenario: FsiScenario) -> None:
    scenario.add_course()
    scenario.add_course_event(course=scenario.latest_course)
    event = scenario.latest_event
    scenario.commit()
    session = scenario.session

    coll = CourseNotificationTemplateCollection(
        session, course_event_id=event.id)

    assert coll.course_event is not None
    assert coll.course_event.id == event.id
    # the subscriptions query for the linked event
    assert coll.course_reservations.count() == 0

    # auto-adds the four template types when none exist yet
    coll.auto_add_templates_if_not_existing()
    assert coll.query().count() == 4

    # a second call is a no-op
    coll.auto_add_templates_if_not_existing()
    assert coll.query().count() == 4
