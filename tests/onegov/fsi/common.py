from __future__ import annotations

import pytz

from datetime import timedelta, datetime
from onegov.core.crypto import hash_password
from onegov.fsi.models import (
    CourseAttendee, Course, CourseEvent, CourseSubscription)
from onegov.fsi.models.course_notification_template import (
    InfoTemplate, SubscriptionTemplate, ReminderTemplate,
    CancellationTemplate)
from onegov.user import User
from uuid import uuid4


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from typing import TypeAlias

    AnyTemplate: TypeAlias = (
        InfoTemplate
        | SubscriptionTemplate
        | CancellationTemplate
        | ReminderTemplate
    )

global_password = 'hunter2'
hashed_password = hash_password(global_password)


TEMPLATE_MODEL_MAPPING: dict[str, type[AnyTemplate]] = {
    'info': InfoTemplate,
    'reservation': SubscriptionTemplate,
    'cancellation': CancellationTemplate,
    'reminder': ReminderTemplate
}


def collection_attr_eq_test(collection: Any, other_collection: Any) -> None:
    # Tests a collection of the method page_by_index duplicates all attrs
    for key in collection.__dict__:
        if key in ('page', 'cached_subset', 'batch'):
            continue
        assert getattr(collection, key) == getattr(other_collection, key)


def admin_factory(session: Session) -> User:
    admin = session.query(User).filter_by(
        username='admin@example.org').first()
    if admin is None:
        admin = User(
            username='admin@example.org',
            password_hash=hashed_password,
            role='admin'
        )
        session.add(admin)
        session.flush()
    return admin


def editor_factory(session: Session) -> User:
    editor = session.query(User).filter_by(
        username='editor@example.org').first()
    if editor is None:
        editor = User(
            username='editor@example.org',
            password_hash=hashed_password,
            role='editor'
        )
        session.add(editor)
        session.flush()
    return editor


def admin_attendee_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseAttendee, dict[str, Any]]:
    # aka Kursverantwortlicher, is an admin, has admin email
    user = admin_factory(session)
    data = {
        'first_name': 'P',
        'last_name': 'P',
        'user_id': user.id
    }

    data.update(**kwargs)
    planner = session.query(CourseAttendee).filter_by(**data).first()
    if planner is None:
        planner = CourseAttendee(**data)
        session.add(planner)
        session.flush()
    return planner, data


def editor_attendee_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseAttendee, dict[str, Any]]:
    # aka Kursverantwortlicher, is an admin, has admin email
    user = editor_factory(session)
    data = {
        'first_name': 'PE',
        'last_name': 'PE',
        'user_id': user.id
    }
    data.update(**kwargs)
    planner = session.query(CourseAttendee).filter_by(**data).first()
    if planner is None:
        planner = CourseAttendee(**data)
        session.add(planner)
        session.flush()
    return planner, data


def member_factory(session: Session) -> User:
    member = session.query(User).filter_by(
        username='member@example.org').first()
    if not member:
        member = User(
            username='member@example.org',
            password_hash=hashed_password,
            role='member'
        )
        session.add(member)
        session.flush()
    return member


def attendee_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseAttendee, dict[str, Any]]:
    user = member_factory(session)
    data = {
        'first_name': 'F',
        'last_name': 'L',
        'user_id': user.id
    }
    data.update(**kwargs)
    attendee = session.query(CourseAttendee).filter_by(
        **data).first()
    if attendee is None:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


def external_attendee_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseAttendee, dict[str, Any]]:
    attendee = session.query(CourseAttendee).filter_by(
        email='external@example.org').first()
    data = {
        'first_name': 'E',
        'last_name': 'E',
        'email': 'external@example.org'
    }
    data.update(**kwargs)
    if attendee is None:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


def course_factory(
    session: Session,
    **kwargs: Any
) -> tuple[Course, dict[str, Any]]:
    data = {
        'name': 'Course',
        'description': 'Description',
        'mandatory_refresh': True,
        'refresh_interval': 1
    }
    data.update(**kwargs)
    course = session.query(Course).filter_by(**data).first()
    if course is None:
        data['id'] = uuid4()
        course = Course(**data)
        session.add(course)
        session.flush()
    return course, data


def course_event_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseEvent, dict[str, Any]]:
    course_ = course_factory(session)
    start = datetime(1950, 1, 1, tzinfo=pytz.utc)
    data: dict[str, Any] = {
        'course_id': course_[0].id,
        'location': 'Room42',
        'start': start,
        'end': start - timedelta(days=30),
        'presenter_name': 'Presenter',
        'presenter_company': 'Company',
        'presenter_email': 'presenter@presenter.org',
        'max_attendees': 20,
    }
    data.update(**kwargs)
    course_event = session.query(CourseEvent).filter_by(**data).first()
    if course_event is None:
        data.setdefault('id', uuid4())
        course_event = CourseEvent(**data)
        session.add_all((
            course_event,
            InfoTemplate(course_event_id=data['id'], text='Info'),
            SubscriptionTemplate(course_event_id=data['id']),
            ReminderTemplate(course_event_id=data['id']),
            CancellationTemplate(course_event_id=data['id'])
        ))
        session.flush()
    return course_event, data


def future_course_event_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseEvent, dict[str, Any]]:
    course_ = course_factory(session)
    in_the_future = datetime(2050, 1, 1, tzinfo=pytz.utc)
    data: dict[str, Any] = {
        'course_id': course_[0].id,
        'location': 'Room42',
        'start': in_the_future,
        'end': in_the_future + timedelta(hours=2),
        'presenter_name': 'Presenter',
        'presenter_company': 'Company',
        'presenter_email': 'presenter@presenter.org',
    }
    data.update(**kwargs)
    course_event = session.query(CourseEvent).filter_by(**data).first()
    if course_event is None:
        data.setdefault('id', uuid4())
        course_event = CourseEvent(**data)
        session.add_all((
            course_event,
            InfoTemplate(course_event_id=data['id'], text='Info'),
            SubscriptionTemplate(course_event_id=data['id']),
            ReminderTemplate(course_event_id=data['id']),
            CancellationTemplate(course_event_id=data['id'])
        ))
        session.flush()
    return course_event, data


def notification_template_factory(
    session: Session,
    **kwargs: Any
) -> tuple[AnyTemplate, dict[str, Any]]:
    kwargs.setdefault('course_event_id', course_event_factory(session)[0].id)
    data: dict[str, Any] = {
        'type': 'reservation',
        'subject': 'Say Hello',
        'text': 'Hello World',
    }
    data.update(**kwargs)
    type = data.pop('type')
    template: AnyTemplate | None = session.query(  # type: ignore[assignment]
        TEMPLATE_MODEL_MAPPING[type]).filter_by(**data).first()
    if template is None:
        template = TEMPLATE_MODEL_MAPPING[type](**data)
        session.add(template)
        session.flush()
    return template, data


def future_course_reservation_factory(
    session: Session,
    **kwargs: Any
) -> tuple[CourseSubscription, dict[str, Any]]:
    data = {
        'course_event_id': future_course_event_factory(session)[0].id,
        'attendee_id': attendee_factory(session)[0].id
    }
    data.update(**kwargs)
    res = session.query(CourseSubscription).filter_by(**data).first()
    if res is None:
        res = CourseSubscription(**data)
        session.add(res)
        session.flush()
    return res, data


class DBMock(NamedTuple):
    attendee: CourseAttendee
    admin_attendee: CourseAttendee
    editor_attendee: CourseAttendee
    course_event: CourseEvent
    future_course_event: CourseEvent
    placeholder: CourseSubscription
    attendee_res: CourseSubscription
    attendee_future_res: CourseSubscription
    planner_res: CourseSubscription
    planner_future_res: CourseSubscription
    empty_course_event: CourseEvent


def db_mock(session: Session) -> DBMock:
    # Create the fixtures with the current session

    in_the_future = datetime(2060, 1, 1, tzinfo=pytz.utc)

    attendee, data = attendee_factory(session, organisation='ORG')
    planner, data = admin_attendee_factory(session)
    planner_editor, data = editor_attendee_factory(
        session, permissions=['ORG']
    )
    course_event, data = course_event_factory(session)
    future_course_event, data = future_course_event_factory(session)
    empty_course_event, data = future_course_event_factory(
        session,
        start=in_the_future,
        end=in_the_future + timedelta(hours=8),
        location='Empty'
    )

    placeholder = CourseSubscription(
        dummy_desc='Placeholder',
        id=uuid4(),
        course_event_id=course_event.id)
    # Create Reservations
    attendee_res = CourseSubscription(
        attendee_id=attendee.id,
        course_event_id=course_event.id
    )

    attendee_future_res = CourseSubscription(
        attendee_id=attendee.id,
        course_event_id=future_course_event.id
    )

    planner_res = CourseSubscription(
        attendee_id=planner.id,
        course_event_id=course_event.id
    )

    planner_future_res = CourseSubscription(
        attendee_id=planner_editor.id,
        course_event_id=future_course_event.id
    )

    session.add_all(
        (
            placeholder, attendee_res, attendee_future_res, planner_res,
            planner_future_res
        )
    )
    session.flush()
    return DBMock(
        attendee, planner, planner_editor, course_event,
        future_course_event, placeholder, attendee_res,
        attendee_future_res, planner_res, planner_future_res,
        empty_course_event
    )
