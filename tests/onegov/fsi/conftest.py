import datetime
from uuid import uuid4

import pytest
import transaction
from sedate import utcnow

from onegov.core.crypto import hash_password
from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course import Course
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.notification_template import FsiNotificationTemplate
from onegov.fsi.models.reservation import Reservation
from onegov.user import User
from onegov.fsi import FsiApp
from onegov.fsi.initial_content import create_new_organisation
from tests.shared.utils import create_app
from tests.onegov.org.conftest import Client


@pytest.fixture(scope='session')
def hashed_password():
    return hash_password('test_password')


@pytest.yield_fixture(scope='function')
def fsi_app(request, hashed_password):
    yield create_fsi_app(request, False, hashed_password)


@pytest.yield_fixture(scope='function')
def es_fsi_app(request, hashed_password):
    yield create_fsi_app(request, True, hashed_password)


@pytest.fixture(scope='function')
def client(fsi_app):
    return Client(fsi_app)


@pytest.fixture(scope='function')
def client_with_es(es_fsi_app):
    return Client(es_fsi_app)


@pytest.fixture(scope='function')
def admin(session, hashed_password):
    def _admin(session):
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
    return _admin


@pytest.fixture(scope='function')
def member(session, hashed_password):
    def _member(session):
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
    return _member


@pytest.fixture(scope='function')
def notification_template(planner, course_event):
    # creator by a notification template
    def _notification_template(session, **kwargs):
        template = session.query(FsiNotificationTemplate).filter_by(
            text='Hello World').first()
        data = dict(
            owner_id=planner(session).id,
            subject='Say Hello',
            text='Hello World',
            course_event_id=course_event(session)[0].id
        )
        data.update(**kwargs)
        if not template:
            template = FsiNotificationTemplate(**data)
            session.add(template)
            session.flush()
        return template, data
    return _notification_template


@pytest.fixture(scope='function')
def course():
    def _course(session, **kwargs):
        data = dict(
            description='Desc',
            name='Course',
            presenter_name='Pres',
            presenter_company='Company',
            mandatory_refresh=True,
            refresh_interval=datetime.timedelta(days=30))
        data.update(**kwargs)
        course = Course(**data)
        session.add(course)
        session.flush()
        return course, data
    return _course


@pytest.fixture(scope='function')
def course_event(course):
    def _course_event(session, **kwargs):
        data = dict(
            course_id=course(session)[0].id,
            name='Event',
            start=utcnow() - datetime.timedelta(days=30, hours=2),
            end=utcnow() - datetime.timedelta(days=30),
            presenter_name='Presenter',
            presenter_company='Company',
            max_attendees=20)
        data.update(**kwargs)
        template = notification_template(session)
        course_event = CourseEvent(**data)
        course_event.template = template
        session.add(course_event)
        session.flush()
        return course_event, data
    return _course_event


@pytest.fixture(scope='function')
def future_course_event(course):
    def _future_course_event(session, **kwargs):
        data = dict(
            course_id=course(session)[0].id,
            name='Future Event',
            start=utcnow() + datetime.timedelta(days=7),
            end=utcnow() + datetime.timedelta(days=7, hours=2),
            presenter_name='Presenter',
            presenter_company='Company',
            max_attendees=20,
            schedule_reminder_before=datetime.timedelta(days=8)
        )
        data.update(**kwargs)
        template = notification_template(session)
        course_event = CourseEvent(**data)
        course_event.template = template
        session.add(course_event)
        session.flush()
        return course_event, data
    return _future_course_event


@pytest.fixture(scope='function')
def future_course_reservation(future_course_event, attendee):
    def _future_course_reservation(session, **kwargs):
        data = dict(
            course_event_id=future_course_event(session)[0].id,
            attendee_id=attendee(session)[0].id
        )
        data.update(**kwargs)
        res = Reservation(**data)
        session.add(res)
        session.flush()
        transaction.commit()
        return res, data
    return _future_course_reservation


@pytest.fixture(scope='function')
def future_course_event(course):
    def _future_course_event(session, **kwargs):
        in_a_week = utcnow() + datetime.timedelta(days=7)
        data = dict(
            course_id=course(session)[0].id,
            name='FutureEvent',
            start=in_a_week,
            end=in_a_week + datetime.timedelta(hours=2),
            presenter_name='Presenter',
            presenter_company='Company')
        data.update(**kwargs)
        course_event = CourseEvent(**data)
        session.add(course_event)
        session.flush()
        return course_event, data
    return _future_course_event


@pytest.fixture(scope='function')
def planner(admin):
    def _planner(session, **kwargs):
        # aka Kursverantwortlicher, is an admin
        planner = session.query(CourseAttendee).filter_by(
            email='planner@example.org').first()
        data = dict(
            first_name='P',
            last_name='P',
            email='planner@example.org',
            user_id=admin(session).id
        )
        data.update(**kwargs)
        if not planner:
            planner = CourseAttendee(**data)
            session.add(planner)
            session.flush()
        return planner
    return _planner


@pytest.fixture(scope='function')
def attendee(session, member):
    def _attendee(session, **kwargs):
        attendee = session.query(CourseAttendee).filter_by(
            email='attendee@example.org').first()
        data = dict(
            first_name='F',
            last_name='L',
            email='attendee@example.org',
            address='Address',
            user_id=member(session).id)
        data.update(**kwargs)
        if not attendee:
            attendee = CourseAttendee(**data)
            session.add(attendee)
            session.flush()
        return attendee, data
    return _attendee


@pytest.fixture(scope='function')
def external_attendee(admin):
    def _external_attendee(session, **kwargs):
        attendee = session.query(CourseAttendee).filter_by(
            email='external@example.org').first()
        data = dict(
            first_name='E',
            last_name='E',
            email='external@example.org',
            address='Address')
        data.update(**kwargs)
        if not attendee:
            attendee = CourseAttendee(**data)
            session.add(attendee)
            session.flush()
        return attendee, data
    return _external_attendee


@pytest.fixture(scope='function')
def course_event_data():
    def _course_event_data():
        return dict(
            name='A', presenter_name='P', presenter_company='C', id=uuid4())
    return _course_event_data


@pytest.fixture(scope='function')
def db_mock_session(course_event, attendee):
    def _db_mock_session(session):
        # Create the fixtures with the current session
        attendee_ = attendee(session)
        course_event_ = course_event(session)

        placeholder = Reservation.as_placeholder(
            'Placeholder', id=uuid4(), course_event_id=course_event_[0].id)
        # Create Reservations
        user_res = Reservation(
            attendee_id=attendee_[0].id,
            course_event_id=course_event_[0].id)
        session.add_all((placeholder, user_res))
        session.flush()
        return session
    return _db_mock_session


def create_fsi_app(request, use_elasticsearch, hashed_password):

    app = create_app(
        app_class=FsiApp,
        request=request,
        use_elasticsearch=use_elasticsearch)

    session = app.session()

    org = create_new_organisation(app, name="Kursverwaltung")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.

    session.add(User(
        username='admin@example.org',
        password_hash=hashed_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=hashed_password,
        role='editor'
    ))

    session.add(User(
        username='member@example.org',
        password_hash=hashed_password,
        role='member'
    ))

    transaction.commit()
    session.close_all()

    return app
