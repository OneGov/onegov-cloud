from __future__ import annotations

from onegov.fsi.collections.attendee import CourseAttendeeCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.onegov.fsi.conftest import FsiScenario


def test_attendee_collection_flags_and_equality(
    scenario: FsiScenario
) -> None:
    session = scenario.session

    default = CourseAttendeeCollection(session)
    assert default.unfiltered is True
    assert default.attendee_permissions == []

    external = CourseAttendeeCollection(session, external_only=True)
    assert external.unfiltered is False

    # __eq__ only compares page / external flags
    assert default == CourseAttendeeCollection(session)
    assert default != CourseAttendeeCollection(session, external_only=True)
    assert default != object()

    # page_by_index preserves the filter flags
    other = external.page_by_index(3)
    assert other.page == 3
    assert other.external_only is True


def test_attendee_collection_permissions(scenario: FsiScenario) -> None:
    scenario.add_attendee(role='editor', organisation='A')
    auth: Any = scenario.latest_attendee
    auth.permissions = ['A', 'B']
    scenario.commit()

    coll = CourseAttendeeCollection(scenario.session, auth_attendee=auth)
    assert coll.attendee_permissions == ['A', 'B']


def test_attendee_collection_role_filters(scenario: FsiScenario) -> None:
    scenario.add_attendee(role='admin')
    scenario.add_attendee(role='editor')
    scenario.add_attendee(role='member')
    scenario.commit()
    session = scenario.session

    assert CourseAttendeeCollection(
        session, editors_only=True).query().count() == 1
    assert CourseAttendeeCollection(
        session, admins_only=True).query().count() == 1


def test_attendee_collection_add_from_user_and_by_id(
    scenario: FsiScenario
) -> None:
    user = scenario.add_user(role='member')
    scenario.commit()

    coll = CourseAttendeeCollection(scenario.session)
    attendee = coll.add_from_user(user)
    scenario.session.flush()

    assert attendee.user_id == user.id
    assert attendee.email == user.username

    found = coll.by_id(attendee.id)
    assert found is not None
    assert found.id == attendee.id
