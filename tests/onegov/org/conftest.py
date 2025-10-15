from __future__ import annotations

import onegov.ticket
import os
import transaction
import pytest

from copy import deepcopy
from datetime import date, timedelta
from onegov.chat import MessageCollection
from onegov.core.elements import Element
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.core.utils import Bunch, module_path
from onegov.form import (
    Form,
    FormDefinitionCollection,
    FormCollection,
    FormSubmission,
)
from onegov.org import OrgApp
from onegov.org.initial_content import create_new_organisation
from onegov.org.layout import DefaultLayout
from onegov.org.models import TicketMessage
from onegov.org.views.ticket import delete_ticket
from onegov.ticket import TicketCollection, Handler
from onegov.user import User
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.scenario import BaseScenario
from tests.shared.utils import create_app
from uuid import uuid4
from yaml import dump


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from libres.db.models import Allocation
    from onegov.core.orm import SessionManager
    from onegov.event import Event
    from onegov.form import FormDefinition, FormRegistrationWindow
    from onegov.org.models import ExtendedDirectory
    from onegov.org.request import OrgRequest
    from onegov.reservation import Reservation
    from onegov.ticket import Ticket
    from onegov.ticket.handler import HandlerRegistry
    from sqlalchemy.orm import Session
    from tests.shared.browser import ExtendedBrowser
    from tests.shared.client import ExtendedResponse
    from typing import Protocol
    from uuid import UUID

    _OrgAppT = TypeVar(
        '_OrgAppT',
        bound=OrgApp,
        default='TestOrgApp',
        covariant=True
    )

    class _ReserveFunc(Protocol):
        def __call__(
            self,
            start: str = ...,
            end: str = ...,
            quota: int = 1,
            whole_day: bool = ...,
        ) -> ExtendedResponse: ...

    class _RenderFunc(Protocol):
        def __call__(self, element: Element) -> ExtendedResponse: ...
else:
    _OrgAppT = TypeVar('_OrgAppT', bound=OrgApp)


class TestOrgApp(OrgApp):
    __test__ = False
    maildir: str


@pytest.fixture(scope='function')
def cfg_path(
    postgres_dsn: str,
    session_manager: SessionManager,
    temporary_directory: str,
    redis_url: str
) -> str:
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url
                },
                'websockets': {
                    'client_url': 'ws://localhost:8766',
                    'manage_url': 'ws://localhost:8766',
                    'manage_token': 'super-super-secret-token'
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = os.path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))
    return cfg_path


class Client(BaseClient[_OrgAppT]):
    skip_n_forms = 1
    use_intercooler = True

    def bound_reserve(self, allocation: Allocation) -> _ReserveFunc:

        default_start = f'{allocation.start:%H:%M}'
        default_end = f'{allocation.end:%H:%M}'
        default_whole_day = allocation.whole_day
        resource = allocation.resource
        allocation_id = allocation.id

        def reserve(
            start: str = default_start,
            end: str = default_end,
            quota: int = 1,
            whole_day: bool = default_whole_day
        ) -> ExtendedResponse:
            return self.post(
                f'/allocation/{resource}/{allocation_id}/reserve'
                f'?start={start}&end={end}&quota={quota}'
                f'&whole_day={whole_day and "1" or "0"}'
            )

        return reserve


@pytest.fixture(scope='function')
def handlers() -> Iterator[HandlerRegistry]:
    before = onegov.ticket.handlers.registry
    onegov.ticket.handlers.registry = {}
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = before


@pytest.fixture(scope='function')
def org_app(request: pytest.FixtureRequest) -> Iterator[TestOrgApp]:
    yield create_org_app(request, enable_search=False)


@pytest.fixture(scope='function')
def wil_app(request: pytest.FixtureRequest) -> Iterator[TestOrgApp]:
    yield create_org_app(request, org_name='Stadt Wil',
                         enable_search=False)


@pytest.fixture(scope='function')
def fts_org_app(request: pytest.FixtureRequest) -> Iterator[TestOrgApp]:
    yield create_org_app(request, enable_search=True)


@pytest.fixture(scope='function')
def client(org_app: TestOrgApp) -> Client[TestOrgApp]:
    return Client(org_app)


@pytest.fixture(scope='function')
def client_with_fts(fts_org_app: TestOrgApp) -> Client[TestOrgApp]:
    return Client(fts_org_app)


@pytest.fixture(scope='function')
def browser(
    browser: ExtendedBrowser,
    org_app_url: str
) -> Iterator[ExtendedBrowser]:
    browser.baseurl = org_app_url
    yield browser


@pytest.fixture(scope='function')
def org_app_url(
    request: pytest.FixtureRequest,
    org_app: TestOrgApp
) -> Iterator[str]:
    org_app.print_exceptions = True
    server = WSGIServer(application=org_app)
    server.start()
    yield server.url
    server.stop()


def create_org_app(
    request: pytest.FixtureRequest,
    org_name: str = 'Govikon',
    enable_search: bool = False,
    cls: type[_OrgAppT] = TestOrgApp  # type: ignore[assignment]
) -> _OrgAppT:
    app = create_app(
        cls,
        request,
        enable_search=enable_search,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    app.configure_payment_providers(
        payment_providers_enabled=True,
        payment_provider_defaults={
            'stripe_connect': {
                'client_id': 'foo',
                'client_secret': 'foo',
                'oauth_gateway': 'https://oauth.example.org',
                'oauth_gateway_auth': 'foo',
                'oauth_gateway_secret': 'bar'
            }
        }
    )
    session = app.session()

    org = create_new_organisation(app, name=org_name, create_files=False)
    domain = org_name.replace(' ', '').strip()
    domain = domain.lower()
    org.meta['reply_to'] = f'mails@{domain}.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.
    test_password = request.getfixturevalue('test_password')

    session.add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=test_password,
        role='editor'
    ))
    session.add(User(
        username='supporter@example.org',
        password_hash=test_password,
        role='supporter'
    ))
    session.add(User(
        username='member@example.org',
        password_hash=test_password,
        role='member'
    ))

    transaction.commit()
    close_all_sessions()

    return app


@pytest.fixture(scope='function')
def render_element(request: pytest.FixtureRequest) -> _RenderFunc:
    class App(OrgApp):
        element: Element

    @App.path(path='/element', model=Element)
    def get_element(app: App) -> Element:
        return app.element

    @App.html(model=Element)
    def render_element(self: Element, request: OrgRequest) -> str:
        return self(DefaultLayout(getattr(self, 'model', None), request))

    app = create_org_app(request, enable_search=False, cls=App)
    client = Client(app)

    def render(element: Element) -> ExtendedResponse:
        app.element = element
        return client.get('/element')

    return render


class Scenario(BaseScenario):
    cached_attributes = (
        'tickets',
        'forms',
        'form_submissions',
        'users',
        'directories',
        'events',
        'reservations',
    )

    tickets: list[Ticket]
    forms: list[FormDefinition]
    form_submissions: list[FormSubmission]
    registration_windows: list[FormRegistrationWindow]
    users: list[User]
    directories: list[ExtendedDirectory]
    events: list[Event]
    reservations: list[Reservation]
    request: Any

    def __init__(
        self,
        session: Session,
        test_password: str,
        handler_code: str | None = None,
        client: Client | None = None
    ) -> None:
        super().__init__(session, test_password)
        self.session = session
        self.handler_code = handler_code
        self.tickets_c = TicketCollection(self.session)
        self.messages_c = MessageCollection(self.session)
        self.form_definitions_ = FormDefinitionCollection(self.session)
        self.forms_c = FormCollection(self.session)

        self.tickets = []
        self.forms = []
        self.form_submissions = []
        self.registration_windows = []
        self.users = []
        self.directories = []
        self.events = []
        self.reservations = []

        self.admin = session.query(User).filter_by(role='admin').first()
        self.member = session.query(User).filter_by(role='member').first()
        self.ticket_state = None
        self.request = Bunch(
            session=self.session,
            translate=lambda x: x,
            is_admin=True,
            assert_valid_csrf_token=lambda: True,
            warning=lambda x: str(x),
            success=lambda x: str(x)
        )
        self.client = client

    def add_user(self, **kwargs: Any) -> User:
        user = self.add(User, password=self.test_password, **kwargs)
        self.users.append(user)
        return user

    def add_admin(self, username: str = 'admin@example.org') -> User:
        return self.add_user(role='admin', username=username)

    def add_member(self, username: str = 'member@example.org') -> User:
        return self.add_user(role='member', username=username)

    def handler_data_FRM(self, **options: Any) -> dict[str, Any]:
        return {}

    def handler_data_EVN(self, **options: Any) -> dict[str, Any]:
        return {}

    def handler_data_DIR(self, **options: Any) -> dict[str, Any]:
        # can also be empty
        return {
            'state': options.get('state', 'adopted'),
            'directory': options.get('directory'),
            'entry_name': options.get('entry_name')
        }

    def handler_data_AGN(self, **options: Any) -> dict[str, Any]:
        return {}

    def handler_data_RSV(self, **options: Any) -> dict[str, Any]:
        return {}

    def handler_data(self, **options: Any) -> dict[str, Any]:
        return getattr(self, f'handler_data_{self.handler_code}')(**options)

    # FIXME: add_ticket seems kinda broken, do we even use it?
    def add_ticket(
        self,
        obj: object | None = None,
        handler_id: str | None = None,
        **handler_data: Any
    ) -> Ticket:
        ticket: Ticket = getattr(self, f'add_ticket_{self.handler_code}')(
            obj=obj, handler_id=handler_id, **handler_data
        )
        self.tickets.append(ticket)
        return ticket

    def add_ticket_FRM(
        self,
        submission: FormSubmission | None = None,
        handler_id: str | None = None,
        owner: User | None = None,
        **handler_data: Any
    ) -> Ticket:
        """ Adds a ticket for the latest form submission """

        if not handler_id:
            submission = submission or self.latest_form_submission
            assert submission is not None
            handler_id = str(submission.id)

        assert handler_id
        assert self.handler_code
        owner = owner or self.latest_user
        assert owner is not None
        self.request.current_username = owner.username

        with self.session.no_autoflush:
            ticket = TicketCollection(self.session).open_ticket(
                handler_code=self.handler_code,
                handler_id=handler_id,
                **handler_data
            )
            TicketMessage.create(ticket, self.request, 'opened')
        return ticket

    def add_form(self, **kwargs: Any) -> FormDefinition:
        title = kwargs.get('title')
        if not title:
            kwargs['title'] = 'A-1'
            kwargs.setdefault('name', 'a')
        kwargs.setdefault('definition', 'E-Mail * = @@@')

        form = self.form_definitions_.add(
            type='custom',
            **kwargs
        )
        self.forms.append(form)
        return form

    def add_reservations(self) -> None:
        pass

    def add_directory(self) -> None:
        pass

    def add_registration_window(
        self,
        form: FormDefinition | None = None,
        **kwargs: Any
    ) -> FormRegistrationWindow:

        form = form or self.latest_form
        assert form is not None

        today = date.today()
        kwargs.setdefault('start', today)
        kwargs.setdefault('end', kwargs['start'] + timedelta(days=10))

        window = form.add_registration_window(**kwargs)
        self.registration_windows.append(window)
        return window

    def add_form_submission(
        self,
        definition: FormDefinition | None = None,
        user: User | None = None,
        window_id: UUID | None = None,
        **kwargs: Any
    ) -> FormSubmission:
        """ Create a form submission for the definition definition. Only
        supports adding submission for existing definitions. And we dont
        care about the submission content.
        """
        if not definition:
            definition = self.latest_form
        assert definition is not None

        window = definition.current_registration_window
        if not window_id and window:
            window_id = window.id

        user = user or self.latest_user
        assert user is not None

        state = kwargs.get('state', 'complete')
        email = kwargs.get('email', user.username)
        meta = kwargs.get('meta')
        spots = kwargs.get('spots', 1)
        title = kwargs.get('title', 'FormSubmission')

        submission_class = FormSubmission.get_polymorphic_class(
            state, FormSubmission
        )
        submission = submission_class()
        submission.id = uuid4()
        submission.title = title
        submission.name = definition.name
        submission.state = state
        submission.meta = meta or {}
        submission.email = email
        submission.registration_window_id = window_id
        submission.spots = spots
        submission.payment_method = 'manual'
        submission.definition = definition.definition

        submission.extensions = definition.extensions
        self.session.add(submission)

        # skip adding data

        self.session.flush()

        self.form_submissions.append(submission)

        return submission

    def accept_ticket(
        self,
        ticket: Ticket | None = None,
        user: User | None = None
    ) -> None:
        ticket = ticket or self.latest_ticket
        assert ticket is not None
        user = user or self.latest_user
        assert user is not None
        ticket.accept_ticket(user)

    def close_ticket(self, ticket: Ticket | None = None) -> None:
        ticket = ticket or self.latest_ticket
        assert ticket is not None
        ticket.close_ticket()

    def reopen_ticket(
        self,
        ticket: Ticket | None = None,
        user: User | None = None
    ) -> None:
        ticket = ticket or self.latest_ticket
        assert ticket is not None
        user = user or self.latest_user
        assert user is not None
        ticket.reopen_ticket(user)

    def delete_ticket(self, ticket: Ticket | None = None) -> None:
        """Using the view function allows to check for
        TicketDeletionError's """
        ticket = ticket or self.tickets[-1]
        assert ticket is not None
        request = deepcopy(self.request)
        request.POST = {'submitted', '1'}
        delete_ticket(ticket, request, Form())

    @property
    def latest_form(self) -> FormDefinition | None:
        return self.forms[-1] if self.forms else None

    @property
    def latest_user(self) -> User | None:
        return self.users[-1] if self.users else None

    @property
    def latest_form_submission(self) -> FormSubmission | None:
        return self.form_submissions[-1] if self.form_submissions else None

    @property
    def latest_ticket(self) -> Ticket | None:
        return self.tickets[-1] if self.tickets else None


@pytest.fixture()
def scenario(
    request: pytest.FixtureRequest,
    client: Client[TestOrgApp]
) -> Scenario:
    test_password = request.getfixturevalue('test_password')
    return Scenario(client.app.session(), test_password, client=client)


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(OrgApp)


class EchoHandler(Handler):

    @property
    def deleted(self) -> bool:
        return False

    @property
    def email(self) -> str | None:
        return self.data.get('email')

    @property
    def title(self) -> Any:
        return self.data.get('title')

    @property
    def subtitle(self) -> str | None:
        return self.data.get('subtitle')

    @property
    def group(self) -> str | None:
        return self.data.get('group')

    def get_summary(self, request: object) -> Any:
        return self.data.get('summary')

    def get_links(self, request: object) -> Any:
        return self.data.get('links')


class LimitingHandler(Handler):

    @property
    def deleted(self) -> bool:
        return False

    @property
    def title(self) -> str:
        return 'Foo'

    @property
    def subtitle(self) -> str:
        return '0xdeadbeef'

    @property
    def group(self) -> str:
        return 'Bar'

    @property
    def handler_id(self) -> int:
        return 1

    @property
    def handler_data(self) -> dict[str, Any]:
        return {}

    @property
    def email(self) -> str:
        return 'foo@bar.com'

    def get_summary(self, request: object) -> Any:
        return 'foobar'

    @classmethod
    def handle_extra_parameters(
        cls,
        session: object,
        query: Any,
        extra_parameters: Any
    ) -> Any:
        if 'limit' in extra_parameters:
            return query.limit(extra_parameters['limit'])
        else:
            return query


@pytest.fixture(scope='session')
def firebase_json() -> Iterator[str]:
    json = 'firebase.json'
    json_path = module_path('tests.onegov.org', '/fixtures/' + json)

    with open(json_path, 'r') as f:
        yield f.read()
