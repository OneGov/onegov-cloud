import datetime
from collections import namedtuple
from uuid import uuid4

import pytz
from sedate import utcnow

from onegov.core.crypto import hash_password
from onegov.fsi.models import CourseAttendee, Course, CourseEvent, \
    CourseReservation
from onegov.fsi.models.course_notification_template import InfoTemplate, \
    ReservationTemplate, ReminderTemplate, CancellationTemplate
from onegov.user import User

global_password = 'hunter2'
hashed_password = hash_password(global_password)


TEMPLATE_MODEL_MAPPING = dict(
    info=InfoTemplate, reservation=ReservationTemplate,
    cancellation=CancellationTemplate, reminder=ReminderTemplate
)


def collection_attr_eq_test(collection, other_collection):
    # Tests a collection of the method page_by_index duplicates all attrs
    for key in collection.__dict__:
        if key in ('page', 'cached_subset', 'batch'):
            continue
        assert getattr(collection, key) == getattr(other_collection, key)


def admin_factory(session):
    admin = session.query(User).filter_by(
        username='admin@example.org').first()
    if not admin:
        admin = User(
            username='admin@example.org',
            password_hash=hashed_password,
            role='admin'
        )
        session.add(admin)
        session.flush()
    return admin


def editor_factory(session):
    editor = session.query(User).filter_by(
        username='editor@example.org').first()
    if not editor:
        editor = User(
            username='editor@example.org',
            password_hash=hashed_password,
            role='editor'
        )
        session.add(editor)
        session.flush()
    return editor


def planner_factory(session, **kwargs):
    # aka Kursverantwortlicher, is an admin, has admin email
    user = admin_factory(session)
    data = dict(
        first_name='P',
        last_name='P',
        user_id=user.id
    )

    data.update(**kwargs)
    planner = session.query(CourseAttendee).filter_by(**data).first()
    if not planner:
        planner = CourseAttendee(**data)
        session.add(planner)
        session.flush()
    return planner, data


def planner_editor_factory(session, **kwargs):
    # aka Kursverantwortlicher, is an admin, has admin email
    user = editor_factory(session)
    data = dict(
        first_name='PE',
        last_name='PE',
        user_id=user.id
    )
    data.update(**kwargs)
    planner = session.query(CourseAttendee).filter_by(**data).first()
    if not planner:
        planner = CourseAttendee(**data)
        session.add(planner)
        session.flush()
    return planner, data


def member_factory(session):
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


def attendee_factory(session, **kwargs):
    user = member_factory(session)
    data = dict(
        first_name='F',
        last_name='L',
        user_id=user.id)
    data.update(**kwargs)
    attendee = session.query(CourseAttendee).filter_by(
        **data).first()
    if not attendee:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


def external_attendee_factory(session, **kwargs):
    attendee = session.query(CourseAttendee).filter_by(
        email='external@example.org').first()
    data = dict(
        first_name='E',
        last_name='E',
        email='external@example.org')
    data.update(**kwargs)
    if not attendee:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


def course_factory(session, **kwargs):
    data = dict(
        name='Course',
        description='Description',
        mandatory_refresh=True,
        refresh_interval=datetime.timedelta(days=365)
    )
    data.update(**kwargs)
    course = session.query(Course).filter_by(**data).first()
    if not course:
        data['id'] = uuid4()
        course = Course(**data)
        session.add(course)
        session.flush()
    return course, data


def course_event_factory(session, **kwargs):
    course_ = course_factory(session)
    data = dict(
        course_id=course_[0].id,
        location='Room42',
        start=utcnow() - datetime.timedelta(days=30, hours=2),
        end=utcnow() - datetime.timedelta(days=30),
        presenter_name='Presenter',
        presenter_company='Company',
        presenter_email='presenter@presenter.org',
        max_attendees=20,
    )
    data.update(**kwargs)
    course_event = session.query(CourseEvent).filter_by(**data).first()
    if not course_event:
        data.setdefault('id', uuid4())
        course_event = CourseEvent(**data)
        session.add_all((
            course_event,
            InfoTemplate(course_event_id=data['id'], text='Info'),
            ReservationTemplate(course_event_id=data['id']),
            ReminderTemplate(course_event_id=data['id']),
            CancellationTemplate(course_event_id=data['id'])
        ))
        session.flush()
    return course_event, data


def future_course_event_factory(session, **kwargs):
    course_ = course_factory(session)
    in_the_future = datetime.datetime(2050, 1, 1, tzinfo=pytz.utc)
    data = dict(
        course_id=course_[0].id,
        location='Room42',
        start=in_the_future,
        end=in_the_future + datetime.timedelta(hours=2),
        presenter_name='Presenter',
        presenter_company='Company',
        presenter_email='presenter@presenter.org',
    )
    data.update(**kwargs)
    course_event = session.query(CourseEvent).filter_by(**data).first()
    if not course_event:
        data.setdefault('id', uuid4())
        course_event = CourseEvent(**data)
        session.add_all((
            course_event,
            InfoTemplate(course_event_id=data['id'], text='Info'),
            ReservationTemplate(course_event_id=data['id']),
            ReminderTemplate(course_event_id=data['id']),
            CancellationTemplate(course_event_id=data['id'])
        ))
        session.flush()
    return course_event, data


def notification_template_factory(session, **kwargs):
    kwargs.setdefault('course_event_id', course_event_factory(session)[0].id)
    data = dict(
        type='reservation',
        subject='Say Hello',
        text='Hello World',
    )
    data.update(**kwargs)
    type = data.pop('type')
    template = session.query(
        TEMPLATE_MODEL_MAPPING[type]).filter_by(**data).first()
    if not template:
        template = TEMPLATE_MODEL_MAPPING[type](**data)
        session.add(template)
        session.flush()
    return template, data


def future_course_reservation_factory(session, **kwargs):
    data = dict(
        course_event_id=future_course_event_factory(session)[0].id,
        attendee_id=attendee_factory(session)[0].id
    )
    data.update(**kwargs)
    res = session.query(CourseReservation).filter_by(**data).first()
    if not res:
        res = CourseReservation(**data)
        session.add(res)
        session.flush()
    return res, data


def db_mock(session):
    # Create the fixtures with the current session

    in_the_future = datetime.datetime(2060, 1, 1, tzinfo=pytz.utc)

    attendee, data = attendee_factory(session, organisation='ORG')
    planner, data = planner_factory(session)
    planner_editor, data = planner_editor_factory(session, permissions=['ORG'])
    course_event, data = course_event_factory(session)
    future_course_event, data = future_course_event_factory(session)
    empty_course_event, data = future_course_event_factory(
        session,
        start=in_the_future,
        end=in_the_future + datetime.timedelta(hours=8),
        location='Empty'
    )

    placeholder = CourseReservation(
        dummy_desc='Placeholder',
        id=uuid4(),
        course_event_id=course_event.id)
    # Create Reservations
    attendee_res = CourseReservation(
        attendee_id=attendee.id,
        course_event_id=course_event.id
    )

    attendee_future_res = CourseReservation(
        attendee_id=attendee.id,
        course_event_id=future_course_event.id
    )

    planner_res = CourseReservation(
        attendee_id=planner.id,
        course_event_id=course_event.id
    )

    planner_future_res = CourseReservation(
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
    return namedtuple(
        'Mock',
        [
            'attendee', 'planner', 'planner_editor', 'course_event',
            'future_course_event', 'placeholder', 'attendee_res',
            'attendee_future_res', 'planner_res', 'planner_future_res',
            'empty_course_event'
        ]
    )(attendee, planner, planner_editor, course_event,
      future_course_event, placeholder, attendee_res,
      attendee_future_res, planner_res, planner_future_res,
      empty_course_event)
