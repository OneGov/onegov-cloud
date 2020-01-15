from uuid import uuid4

import pytest
import transaction

from onegov.fsi.models.course_reservation import CourseReservation
from onegov.user import User
from onegov.fsi import FsiApp
from onegov.fsi.initial_content import create_new_organisation
from tests.onegov.fsi.common import (
    global_password, admin_factory,
    editor_factory, planner_factory, planner_editor_factory, member_factory,
    attendee_factory, external_attendee_factory, notification_template_factory,
    course_factory, course_event_factory, future_course_event_factory,
    future_course_reservation_factory, db_mock)
from tests.onegov.fsi.common import hashed_password as _hashed_password

from tests.shared.utils import create_app
from tests.shared import Client as BaseClient


class Client(BaseClient):

    use_intercooler = True
    skip_first_form = True

    def login_member(self, to=None):
        return self.login('member@example.org', global_password, to)


@pytest.fixture(scope='session')
def plain_password():
    return global_password


@pytest.fixture(scope='session')
def hashed_password():
    return _hashed_password


@pytest.yield_fixture(scope='function')
def fsi_app(request, hashed_password):
    yield create_fsi_app(request, False, hashed_password)


@pytest.yield_fixture(scope='function')
def fsi_app_mocked(request, hashed_password):
    yield create_fsi_app(request, False, hashed_password, mock_db=True)


@pytest.yield_fixture(scope='function')
def es_fsi_app(request, hashed_password):
    yield create_fsi_app(request, True, hashed_password)


@pytest.yield_fixture(scope='function')
def es_fsi_app_mocked(request, hashed_password):
    yield create_fsi_app(request, True, hashed_password, mock_db=True)


@pytest.fixture(scope='function')
def client(fsi_app):
    return Client(fsi_app)


@pytest.fixture(scope='function')
def client_with_es(es_fsi_app):
    return Client(es_fsi_app)


@pytest.fixture(scope='function')
def client_with_db(fsi_app_mocked):
    return Client(fsi_app_mocked)


@pytest.fixture(scope='function')
def client_with_es_db(es_fsi_app_mocked):
    return Client(es_fsi_app_mocked)


@pytest.fixture(scope='function')
def admin():
    return admin_factory


@pytest.fixture(scope='function')
def editor():
    return editor_factory


@pytest.fixture(scope='function')
def planner(admin):
    return planner_factory


@pytest.fixture(scope='function')
def planner_editor(editor):
    return planner_editor_factory


@pytest.fixture(scope='function')
def member():
    return member_factory


@pytest.fixture(scope='function')
def attendee():
    return attendee_factory


@pytest.fixture(scope='function')
def external_attendee():
    return external_attendee_factory


@pytest.fixture(scope='function')
def notification_template(course_event):
    return notification_template_factory


@pytest.fixture(scope='function')
def course():
    return course_factory


@pytest.fixture(scope='function')
def course_event(course):
    return course_event_factory


@pytest.fixture(scope='function')
def future_course_event(course):
    return future_course_event_factory


@pytest.fixture(scope='function')
def future_course_reservation(future_course_event, attendee):
    return future_course_reservation_factory


@pytest.fixture(scope='function')
def course_event_data():
    def _course_event_data():
        return dict(
            name='A',
            presenter_name='P',
            presenter_company='C',
            id=uuid4(),
            description='Some Desc'
        )
    return _course_event_data


@pytest.fixture(scope='function')
def db_mock_session(course_event, attendee):
    def _db_mock_session(session):
        # Create the fixtures with the current session
        attendee_ = attendee(session)
        course_event_ = course_event(session)

        placeholder = CourseReservation(
            dummy_desc='Placeholder',
            id=uuid4(),
            course_event_id=course_event_[0].id)
        # Create Reservations
        user_res = CourseReservation(
            attendee_id=attendee_[0].id,
            course_event_id=course_event_[0].id
        )
        session.add_all((placeholder, user_res))
        session.flush()
        return session
    return _db_mock_session


def create_fsi_app(request, use_elasticsearch, hashed_password, mock_db=False):

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
    if mock_db:
        db_mock(session)

    transaction.commit()
    session.close_all()

    return app
