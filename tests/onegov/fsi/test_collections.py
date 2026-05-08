from __future__ import annotations

from datetime import timedelta
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.models import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from sedate import utcnow
from tests.onegov.fsi.common import collection_attr_eq_test
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from uuid import UUID
    from .conftest import FsiScenario


class AuthAttendee:

    def __init__(
        self,
        role: str | None = None,
        id: UUID | None = None,
        permissions: list[str] | None = None
    ) -> None:
        self.role = role or 'admin'
        self.id = id or uuid4()
        self.permissions = permissions or []


def test_course_collection(scenario: FsiScenario) -> None:
    scenario.add_course(hidden_from_public=True, name='Hidden')
    scenario.add_course()
    course1 = scenario.latest_course
    coll = CourseCollection(scenario.session)
    # collection defaults to not return the hidden_from_public one's
    assert coll.query().count() == 1
    course1.hidden_from_public = True
    assert coll.by_id(course1.id) is not None
    assert coll.query().count() == 0
    coll.show_hidden_from_public = True
    assert coll.query().count() == 2


def test_course_event_collection(
    session: Session,
    scenario: FsiScenario
) -> None:

    now = utcnow()
    course_id = scenario.add_course()
    new_course_events = (
        CourseEvent(
            course_id=course_id,
            location=f'Address, Room {i}',
            start=now + timedelta(days=i),
            end=now + timedelta(days=i, hours=2),
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

    # Test ascending ordering and timestamp mixin
    assert result[0].start < result[1].start

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
    tmr = now + timedelta(days=1)
    event_coll = CourseEventCollection(session, from_date=tmr)
    assert event_coll.query().count() == 1


def test_event_collection_add_placeholder(scenario: FsiScenario) -> None:
    # Test add_placeholder method
    scenario.add_course()
    scenario.add_course_event(course=scenario.latest_course)
    assert scenario.latest_event.attendees.count() == 0


def test_attendee_collection(scenario: FsiScenario) -> None:

    scenario.add_attendee()
    scenario.add_attendee(organisation='A', username='A@A.com')
    assert scenario.latest_attendee.active
    scenario.add_attendee(external=True)

    session = scenario.session

    auth_admin: Any = AuthAttendee(role='admin')

    coll = CourseAttendeeCollection(session, auth_attendee=auth_admin)
    collection_attr_eq_test(coll, coll.page_by_index(1))

    # Get all of them
    assert coll.query().count() == 3

    coll.external_only = True
    assert coll.query().count() == 1

    coll.external_only = False
    coll.exclude_external = True
    assert coll.query().count() == 2

    # Test editors only
    coll = CourseAttendeeCollection(
        session, auth_attendee=auth_admin, editors_only=True)
    assert coll.query().count() == 0

    # Test for role editor
    auth_editor: Any = AuthAttendee(role='editor')
    coll = CourseAttendeeCollection(session, auth_attendee=auth_editor)

    # Get all of them, but himself does not exist
    assert coll.query().count() == 0

    # create and attendee with an editor as user
    scenario.add_attendee(role='editor', id=auth_editor.id)
    assert coll.query().count() == 1

    # check if he can see attendee with organisation
    editor = scenario.latest_attendee
    editor.permissions = ['A']
    coll = CourseAttendeeCollection(session, auth_attendee=editor)
    assert coll.attendee_permissions == ['A']
    assert coll.query().count() == 2


def test_reservation_collection_query(scenario: FsiScenario) -> None:
    session = scenario.session
    scenario.add_attendee(role='admin')

    scenario.add_course()
    scenario.add_course_event(course=scenario.latest_course)

    scenario.add_attendee(role='member')
    att = scenario.latest_attendee
    scenario.add_subscription(scenario.latest_event, att)

    scenario.add_attendee(role='editor')
    editor = scenario.latest_attendee
    scenario.add_subscription(scenario.latest_event, editor)

    scenario.add_attendee(external=True)
    scenario.add_subscription(scenario.latest_event, scenario.latest_attendee)
    scenario.commit()

    auth_attendee: Any = AuthAttendee()

    # unfiltered for admin, must yield all
    coll = SubscriptionsCollection(session, auth_attendee=auth_attendee)
    assert coll.query().count() == 3

    # test filter for attendee_id
    coll = SubscriptionsCollection(
        session,
        auth_attendee=auth_attendee,
        attendee_id=att.id)
    assert coll.query().count() == 1

    # test for course_event_id
    coll = SubscriptionsCollection(
        session,
        auth_attendee=auth_attendee,
        course_event_id=scenario.latest_event.id)
    assert coll.query().count() == 3

    # Test for editor with no permissions should see just his own
    auth_attendee = AuthAttendee(role='editor', id=editor.id)
    coll = SubscriptionsCollection(session, auth_attendee=auth_attendee)
    assert coll.query().count() == 1

    # Add an organisation
    att.organisation = 'A'
    assert coll.auth_attendee is not None
    coll.auth_attendee.permissions = ['A']
    assert coll.query().count() == 1

    # Test editor wants to get his own
    coll = SubscriptionsCollection(
        session, auth_attendee=auth_attendee, attendee_id=editor.id)
    assert coll.query().count() == 1

    # member user_role
    assert coll.auth_attendee is not None
    coll.auth_attendee.role = 'member'  # type: ignore[misc]
    # coll.attendee_id will be set in path like
    coll.attendee_id = att.id
    assert coll.query().count() == 1


def test_ranked_subscription_query(scenario: FsiScenario) -> None:
    scenario.add_attendee(role='member')
    scenario.add_course(
        mandatory_refresh=True,
        refresh_interval=1
    )
    scenario.add_course_event(
        scenario.latest_course, start=utcnow() - timedelta(days=700))

    for i in range(3):
        scenario.add_course_event(scenario.latest_course)
        scenario.add_subscription(
            scenario.latest_event,
            scenario.latest_attendee,
            event_completed=i != 2
        )

    scenario.commit()
    scenario.refresh()

    fake_admin: Any = AuthAttendee()
    audits = AuditCollection(
        scenario.session, scenario.latest_course.id,
        fake_admin
    )
    result = audits.ranked_subscription_query().all()

    assert result[0].start > result[1].start
    assert result[0].rownum == 1
    assert result[1].rownum == 2
    assert result[0].start != scenario.latest_event.start


def test_audit_collection(scenario: FsiScenario) -> None:

    scenario.add_course(
        mandatory_refresh=True,
        refresh_interval=1
    )
    for i in range(6):
        scenario.add_course_event(scenario.latest_course)

    orgs = ['AA', 'BB', None]
    for i, org in enumerate(orgs):
        scenario.add_attendee(
            role='member',
            organisation=org,
            username=f'{i}.{org or "ZZZ"}@email.com'
        )
        scenario.add_subscription(
            scenario.course_events[i],
            scenario.attendees[i],
            event_completed=True
        )
        # Add not completed courses more recent, should be discarded in query
        scenario.add_subscription(
            scenario.course_events[i + 3],
            scenario.attendees[i],
            event_completed=False
        )
    # add some noise
    scenario.add_course_event(scenario.latest_course)
    scenario.add_attendee(external=True, username='h.r@giger.ch')

    # Add inactive attendee
    scenario.add_attendee(active=False)

    scenario.commit()
    scenario.refresh()

    # ---- Check preparing query last_subscriptions ----
    fake_admin: Any = AuthAttendee()
    fake_editor: Any = AuthAttendee(role='editor', permissions=['AA'])

    audits = AuditCollection(
        scenario.session, scenario.latest_course.id,
        fake_admin
    )
    results = tuple(
        (e.attendee_id, e.start) for e in
        audits.last_subscriptions()
    )

    # Hide future subscriptions
    assert not results

    # Change all event dates to the past
    for event in scenario.course_events:
        event.start -= timedelta(days=5 * 365)
        event.end -= timedelta(days=5 * 365)

    scenario.commit()
    scenario.refresh()

    results = tuple(
        (e.attendee_id, e.start) for e in
        audits.last_subscriptions()
    )

    assert sorted(results) == sorted(
        (a.id, e.start) for a, e in
        zip(scenario.active_attendees, scenario.course_events[:3])
    )

    # add a subscription also for this attendee, but not completed
    scenario.add_subscription(
        scenario.course_events[3],
        scenario.latest_attendee
    )
    scenario.commit()
    scenario.refresh()
    query = audits.last_subscriptions()
    # Check if his subscription is added even if its not marked completed
    assert len(results) + 1 == query.count()

    # Check filtering for admin obtaining all records

    def get_filtered() -> Query[CourseAttendee]:
        return audits.filter_attendees_by_role(all_atts_in_db)

    all_atts_in_db = scenario.session.query(CourseAttendee)
    assert get_filtered().count() == len(scenario.attendees)

    audits.organisations = ['AA']
    # also do not return the ones without org for admins
    assert get_filtered().count() == 1

    # just the ones he has permissions, no more
    audits.auth_attendee = fake_editor
    assert get_filtered().count() == 1

    # Test filtering with alphabetical letter

    # ---- Check actual query joining filtered attendees ----
    # Check for admin
    audits.auth_attendee = fake_admin
    audits.organisations = []
    assert audits.query().count() == len(scenario.active_attendees)
    audits.organisations = ['AA']
    assert audits.query().count() == 1
    # get the one having ln starting with ZZZ
    audits.letter = 'Z'
    # Currently and att without org disregarded with a org filter
    assert audits.query().count() == 0
    audits.organisations = []
    assert audits.query().count() == 1
