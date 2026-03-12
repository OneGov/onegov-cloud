from __future__ import annotations

import pytest
import transaction

from datetime import timedelta
from uuid import uuid4
from faker import Faker
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.fsi.models import CourseAttendee, Course, CourseEvent
from onegov.fsi.models.course_notification_template import (
    InfoTemplate, SubscriptionTemplate,
    CancellationTemplate, ReminderTemplate)
from onegov.fsi.models.course_subscription import CourseSubscription
from onegov.user import User
from onegov.fsi import FsiApp
from onegov.fsi.initial_content import create_new_organisation
from sedate import utcnow
from sqlalchemy import desc
from sqlalchemy.orm.session import close_all_sessions
from tests.onegov.fsi.common import (
    global_password, admin_factory,
    editor_factory, admin_attendee_factory, editor_attendee_factory,
    member_factory,
    attendee_factory, external_attendee_factory, notification_template_factory,
    course_factory, course_event_factory, future_course_event_factory,
    future_course_reservation_factory, db_mock, TEMPLATE_MODEL_MAPPING)
from tests.onegov.fsi.common import hashed_password as _hashed_password
from tests.shared.scenario import BaseScenario
from tests.shared.utils import create_app
from tests.shared import Client as BaseClient


from typing import Any, Protocol, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterator
    from sqlalchemy.orm import Session
    from tests.onegov.fsi.common import AnyTemplate
    from tests.shared.client import ExtendedResponse
    from uuid import UUID

    _T_co = TypeVar('_T_co', covariant=True)
    _FsiAppT = TypeVar(
        '_FsiAppT',
        bound=FsiApp,
        default='TestFsiApp',
        covariant=True
    )

    class Factory(Protocol[_T_co]):
        def __call__(
            self,
            session: Session,
            **kwargs: Any
        ) -> tuple[_T_co, dict[str, Any]]: ...
else:
    _FsiAppT = TypeVar('_FsiAppT', bound=FsiApp)


class TestFsiApp(FsiApp):
    __test__ = False
    maildir: str


class Client(BaseClient[_FsiAppT]):

    use_intercooler = True
    skip_n_forms = 1

    def login_member(self, to: str | None = None) -> ExtendedResponse:
        return self.login('member@example.org', global_password, to)


@pytest.fixture(scope='session')
def plain_password() -> str:
    return global_password


@pytest.fixture(scope='session')
def hashed_password() -> str:
    return _hashed_password


@pytest.fixture(scope='function')
def fsi_app(
    request: pytest.FixtureRequest,
    hashed_password: str
) -> Iterator[TestFsiApp]:
    yield create_fsi_app(request, False, hashed_password)


@pytest.fixture(scope='function')
def fsi_app_mocked(
    request: pytest.FixtureRequest,
    hashed_password: str
) -> Iterator[TestFsiApp]:
    yield create_fsi_app(request, False, hashed_password, mock_db=True)


@pytest.fixture(scope='function')
def fts_fsi_app(
    request: pytest.FixtureRequest,
    hashed_password: str
) -> Iterator[TestFsiApp]:
    yield create_fsi_app(request, True, hashed_password)


@pytest.fixture(scope='function')
def fts_fsi_app_mocked(
    request: pytest.FixtureRequest,
    hashed_password: str
) -> Iterator[TestFsiApp]:
    yield create_fsi_app(request, True, hashed_password, mock_db=True)


@pytest.fixture(scope='function')
def client(fsi_app: TestFsiApp) -> Client[TestFsiApp]:
    return Client(fsi_app)


@pytest.fixture(scope='function')
def client_with_fts(fts_fsi_app: TestFsiApp) -> Client[TestFsiApp]:
    return Client(fts_fsi_app)


@pytest.fixture(scope='function')
def client_with_db(fsi_app_mocked: TestFsiApp) -> Client[TestFsiApp]:
    return Client(fsi_app_mocked)


@pytest.fixture(scope='function')
def client_with_fts_db(fts_fsi_app_mocked: TestFsiApp) -> Client[TestFsiApp]:
    return Client(fts_fsi_app_mocked)


@pytest.fixture(scope='function')
def admin() -> Callable[[Session], User]:
    return admin_factory


@pytest.fixture(scope='function')
def editor() -> Callable[[Session], User]:
    return editor_factory


@pytest.fixture(scope='function')
def admin_attendee() -> Factory[CourseAttendee]:
    return admin_attendee_factory


@pytest.fixture(scope='function')
def editor_attendee() -> Factory[CourseAttendee]:
    return editor_attendee_factory


@pytest.fixture(scope='function')
def member() -> Callable[[Session], User]:
    return member_factory


@pytest.fixture(scope='function')
def attendee() -> Factory[CourseAttendee]:
    return attendee_factory


@pytest.fixture(scope='function')
def external_attendee() -> Factory[CourseAttendee]:
    return external_attendee_factory


@pytest.fixture(scope='function')
def notification_template() -> Factory[AnyTemplate]:
    return notification_template_factory


@pytest.fixture(scope='function')
def course() -> Factory[Course]:
    return course_factory


@pytest.fixture(scope='function')
def course_event() -> Factory[CourseEvent]:
    return course_event_factory


@pytest.fixture(scope='function')
def future_course_event() -> Factory[CourseEvent]:
    return future_course_event_factory


@pytest.fixture(scope='function')
def future_course_reservation() -> Factory[CourseSubscription]:
    return future_course_reservation_factory


@pytest.fixture(scope='function')
def course_event_data() -> Callable[[], dict[str, Any]]:
    def _course_event_data() -> dict[str, Any]:
        return {
            'name': 'A',
            'presenter_name': 'P',
            'presenter_company': 'C',
            'id': uuid4(),
            'description': 'Some Desc'
        }
    return _course_event_data


@pytest.fixture(scope='function')
def db_mock_session(
    course_event: Factory[CourseEvent],
    attendee: Factory[CourseAttendee]
) -> Callable[[Session], Session]:
    def _db_mock_session(session: Session) -> Session:
        # Create the fixtures with the current session
        attendee_ = attendee(session)
        course_event_ = course_event(session)

        placeholder = CourseSubscription(
            dummy_desc='Placeholder',
            id=uuid4(),
            course_event_id=course_event_[0].id)
        # Create Reservations
        user_res = CourseSubscription(
            attendee_id=attendee_[0].id,
            course_event_id=course_event_[0].id
        )
        session.add_all((placeholder, user_res))
        session.flush()
        return session
    return _db_mock_session


def create_fsi_app(
    request: pytest.FixtureRequest,
    enable_search: bool,
    hashed_password: str,
    mock_db: bool = False
) -> TestFsiApp:

    app = create_app(
        app_class=TestFsiApp,
        request=request,
        enable_search=enable_search,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )

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
    close_all_sessions()

    return app


class FsiScenario(BaseScenario):

    cached_attributes = (
        'users',
        'attendees',
        'courses',
        'course_events',
        'subscriptions',
        'templates'
    )

    users: list[User]
    attendees: list[CourseAttendee]
    courses: list[Course]
    course_events: list[CourseEvent]
    subscriptions: list[CourseSubscription]
    templates: list[AnyTemplate]

    def __init__(self, session: Session, test_password: str) -> None:
        super().__init__(session, test_password)

        self.faker = Faker()
        self.users = []
        self.attendees = []
        self.courses = []
        self.course_events = []
        self.subscriptions = []
        self.templates = []

    def add_attendee(
        self,
        external: bool = False,
        **columns: Any
    ) -> None:

        assert 'first_name' not in columns, 'Provide email to construct'
        assert 'last_name' not in columns, 'Provide email to construct'
        columns.setdefault('username', self.faker.email())
        columns.setdefault('active', True)

        fn, ln = columns['username'].split('@')
        if '.' in fn:
            fn, ln = fn.split('.')

        exclude = ('organisation', 'permissions', 'id')

        if not external:
            if not columns.get('user_id'):
                user = self.add_user(
                    **{k: v for k, v in columns.items() if k not in exclude}
                )
                columns['user_id'] = user.id
            else:
                user = self.session.query(User).filter_by(
                    id=columns['user_id']).one()

            columns.setdefault('source_id', user.source_id)
        else:
            columns.setdefault('_email', columns['username'])

        self.attendees.append(self.add(
            model=CourseAttendee,
            id=columns.get('id', uuid4()),
            user_id=columns.get('user_id'),
            active=columns.get('active'),
            source_id=columns.get('source_id'),
            first_name=fn,
            last_name=ln,
            organisation=columns.get('organisation'),
            permissions=columns.get('permissions', [])
        ))

    def add_user(self, **columns: Any) -> User:
        columns.setdefault('role', 'admin')
        columns.setdefault('username', self.faker.email())

        user = self.add(
            model=User,
            password_hash=self.test_password,
            id=uuid4(),
            **columns
        )
        self.users.append(user)

        user.realname = (
            f'{self.faker.first_name()}\u00A0{self.faker.last_name()}')
        user.data = user.data or {}
        user.data['salutation'] = self.faker.random_element(
            ('mr', 'ms'))
        user.data['address'] = self.faker.address()
        user.data['zip_code'] = self.faker.zipcode()
        user.data['place'] = self.faker.city()
        user.data['political_municipality'] = self.faker.city()
        user.data['emergency'] = f'123 456 789 ({self.faker.name()})'
        return user

    def add_course(
        self,
        add_templates: bool = False,
        **columns: Any
    ) -> UUID:
        columns.setdefault('name', f"Course {len(self.courses)}")
        columns.setdefault('description', 'default description')
        course = self.add(
            Course,
            **columns,
            id=uuid4()
        )
        self.courses.append(course)
        if add_templates:
            data = dict(course_event_id=course.id)
            self.session.add_all((
                InfoTemplate(**data),
                SubscriptionTemplate(**data),
                CancellationTemplate(**data),
                ReminderTemplate(**data)
            ))

        return course.id

    def add_course_event(self, course: Course, **columns: Any) -> CourseEvent:
        columns['course_id'] = course.id
        columns.setdefault('presenter_name', self.faker.name())
        columns.setdefault('presenter_company', self.faker.company())
        columns.setdefault('presenter_email', self.faker.company_email())
        columns.setdefault('location', self.faker.city())

        if 'start' not in columns:
            others = [
                e for e in self.course_events if
                e.course_id == columns['course_id']
            ]
            if others:
                start = others[-1].start + timedelta(days=30)
                columns.setdefault('start', start)
            else:
                start = utcnow() + timedelta(days=1)
            columns.setdefault('start', start)

        columns.setdefault('end', columns['start'] + timedelta(hours=4))

        event = self.add(
            CourseEvent,
            **columns,
            id=uuid4()
        )
        self.course_events.append(event)
        return event

    def add_subscription(
        self,
        event: CourseEvent,
        attendee: CourseAttendee | None,
        **columns: Any
    ) -> CourseSubscription:
        subscription = self.add(
            CourseSubscription,
            **columns,
            course_event_id=event.id,
            attendee_id=attendee.id if attendee else None,
            id=uuid4()
        )
        self.subscriptions.append(subscription)
        return subscription

    def add_notification_template(
        self,
        event: CourseEvent,
        all_types: bool = True,
        **columns: Any
    ) -> list[AnyTemplate]:
        columns.setdefault('text', )
        columns.setdefault('course_event_id', event.id)

        types: Collection[str] = TEMPLATE_MODEL_MAPPING.keys()
        if not all_types:
            columns.setdefault('type', 'reservation')
            columns.setdefault('subject', columns['type'].upper())
            types = (columns['type'], )
            self.templates.append(self.add(  # type: ignore[arg-type]
                TEMPLATE_MODEL_MAPPING[columns['type']],
                **columns,
                id=uuid4()
            ))
        else:
            columns.pop('subject', None)
            for t in types:
                self.templates.append(self.add(  # type: ignore[arg-type]
                    TEMPLATE_MODEL_MAPPING[t],
                    subject=t.upper(),
                    **columns,
                    id=uuid4()
                ))
        return self.templates[-len(types)::]

    def first_user(self, role: str = 'admin') -> User | None:
        return self.session.query(User).filter_by(
            role=role).order_by(desc(User.created)).first()

    @property
    def latest_attendee(self) -> CourseAttendee:
        return self.attendees[-1]

    @property
    def latest_course(self) -> Course:
        return self.courses[-1]

    @property
    def latest_event(self) -> CourseEvent:
        return self.course_events[-1]

    def latest_subscriptions(self, count: int = 1) -> list[CourseSubscription]:
        return self.subscriptions[-count::]

    @property
    def active_attendees(self) -> list[CourseAttendee]:
        return [a for a in self.attendees if a.active]


@pytest.fixture(scope='function')
def scenario(
    request: pytest.FixtureRequest,
    session: Session,
    hashed_password: str
) -> Iterator[FsiScenario]:
    for name in request.fixturenames:
        if name in ('fsi_app', 'fts_fsi_app'):
            session = request.getfixturevalue(name).session()

    yield FsiScenario(session, hashed_password)


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(FsiApp)
