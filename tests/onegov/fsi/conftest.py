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


@pytest.fixture(scope='function')
def member(session, hashed_password):
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


@pytest.fixture(scope='function')
def notification_template(session, planner, course_event):
    # creator by a notification template
    template = session.query(FsiNotificationTemplate).filter_by(
        text='Hello World').first()
    if not template:
        template = FsiNotificationTemplate(
            owner_id=planner.id,
            subject='Say Hello',
            text='Hello World',
            course_event_id=course_event[0].id
        )
        session.add(template)
        session.flush()
    return template


@pytest.fixture(scope='function')
def course(session):
    data = dict(
        description='Desc',
        name='Course',
        presenter_name='Pres',
        presenter_company='Company',
        mandatory_refresh=True,
        refresh_interval=datetime.timedelta(days=30))
    course = Course(**data)
    session.add(course)
    session.flush()
    return course, data


@pytest.fixture(scope='function')
def course_event(session, course):
    data = dict(
        course_id=course[0].id,
        name='Event',
        start=utcnow() - datetime.timedelta(days=30, hours=2),
        end=utcnow() - datetime.timedelta(days=30),
        presenter_name='Presenter',
        presenter_company='Company',
        max_attendees=20)
    course_event = CourseEvent(**data)
    session.add(course_event)
    session.flush()
    return course_event, data


@pytest.fixture(scope='function')
def future_course_event(session, course):
    data = dict(
        course_id=course[0].id,
        name='Future Event',
        start=utcnow() + datetime.timedelta(days=7),
        end=utcnow() + datetime.timedelta(days=7, hours=2),
        presenter_name='Presenter',
        presenter_company='Company',
        max_attendees=20,
        schedule_reminder_before=datetime.timedelta(days=8)
    )
    course_event = CourseEvent(**data)
    session.add(course_event)
    session.flush()
    return course_event, data


@pytest.fixture(scope='function')
def future_course_reservation(session, future_course_event, attendee):
    data = dict(
        course_event_id=future_course_event[0].id,
        attendee_id=attendee[0].id
    )
    res = Reservation(**data)
    session.add(res)
    session.flush()
    return res, data


@pytest.fixture(scope='function')
def future_course_event(session, course):
    in_a_week = utcnow() + datetime.timedelta(days=7)
    data = dict(
        course_id=course[0].id,
        name='FutureEvent',
        start=in_a_week,
        end=in_a_week + datetime.timedelta(hours=2),
        presenter_name='Presenter',
        presenter_company='Company')
    course_event = CourseEvent(**data)
    session.add(course_event)
    session.flush()
    return course_event, data


@pytest.fixture(scope='function')
def planner(session, admin):
    # aka Kursverantwortlicher, is an admin
    planner = session.query(CourseAttendee).filter_by(
        email='planner@example.org').first()
    if not planner:
        planner = CourseAttendee(
            first_name='P',
            last_name='P',
            email='planner@example.org',
            user_id=admin.id)
        session.add(planner)
        session.flush()
    return planner


@pytest.fixture(scope='function')
def attendee(session, member):
    attendee = session.query(CourseAttendee).filter_by(
        email='attendee@example.org').first()
    data = dict(
        first_name='F',
        last_name='L',
        email='attendee@example.org',
        address='Address',
        user_id=member.id)
    if not attendee:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


@pytest.fixture(scope='function')
def external_attendee(session, admin):
    attendee = session.query(CourseAttendee).filter_by(
        email='external@example.org').first()
    data = dict(
        first_name='E',
        last_name='E',
        email='external@example.org',
        address='Address')
    if not attendee:
        attendee = CourseAttendee(**data)
        session.add(attendee)
        session.flush()
    return attendee, data


@pytest.fixture(scope='function')
def mock_data_course_event():
    def _mock_data_course_event():
        return dict(
            name='A', presenter_name='P', presenter_company='C', id=uuid4())
    return _mock_data_course_event


@pytest.fixture(scope='function')
def db_mock_session(
        session, course_event, course, attendee):
    placeholder = Reservation.as_placeholder(
        'Placeholder', id=uuid4(), course_event_id=course_event[0].id)
    # Create Reservations
    user_res = Reservation(
        attendee_id=attendee[0].id,
        course_event_id=course_event[0].id)
    session.add_all((placeholder, user_res))
    session.flush()
    return session


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
