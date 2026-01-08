from __future__ import annotations

import onegov.ticket
import pytest
import transaction

from onegov.core.utils import module_path
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.town6 import TownApp
from onegov.town6.initial_content import builtin_form_definitions
from onegov.town6.initial_content import create_new_organisation
from onegov.user import User
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from libres.db.models import Allocation
    from onegov.ticket.handler import HandlerRegistry
    from tests.shared.browser import ExtendedBrowser
    from tests.shared.client import ExtendedResponse
    from typing import Protocol

    _TownAppT = TypeVar(
        '_TownAppT',
        bound=TownApp,
        default='TestTownApp',
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
else:
    _TownAppT = TypeVar('_OrgAppT', bound=TownApp)


class TestTownApp(TownApp):
    __test__ = False
    maildir: str


class Client(BaseClient[_TownAppT]):
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


@pytest.fixture(scope='session')
def forms() -> Iterator[list[tuple[str, str, str]]]:
    yield list(builtin_form_definitions(
        module_path('onegov.town6', 'forms/builtin/de')))


@pytest.fixture(scope='function')
def town_app(request: pytest.FixtureRequest) -> Iterator[TestTownApp]:
    yield create_town_app(request, enable_search=False)


@pytest.fixture(scope='function')
def client(town_app: TestTownApp) -> Client[TestTownApp]:
    return Client(town_app)


@pytest.fixture(scope='function')
def browser(
    browser: ExtendedBrowser,
    town_app_url: str
) -> Iterator[ExtendedBrowser]:
    browser.baseurl = town_app_url
    yield browser


@pytest.fixture(scope='function')
def town_app_url(
    request: pytest.FixtureRequest,
    town_app: TestTownApp
) -> Iterator[str]:
    town_app.print_exceptions = True
    server = WSGIServer(application=town_app)
    server.start()
    yield server.url
    server.stop()


@pytest.fixture(scope='function')
def fts_town_app(request: pytest.FixtureRequest) -> Iterator[TestTownApp]:
    yield create_town_app(request, enable_search=True)


@pytest.fixture(scope='function')
def client_with_fts(fts_town_app: TestTownApp) -> Client[TestTownApp]:
    client = Client(fts_town_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


def create_town_app(
    request: pytest.FixtureRequest,
    enable_search: bool = False
) -> TestTownApp:

    app = create_app(
        TestTownApp,
        request,
        enable_search,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    app.configure_analytics_providers(
        analytics_providers={
            'plausible': {
                'provider': 'plausible',
                'title': 'Dummy',
                'script_src': 'https://dummy-plausible.test/script.js',
            },
            'matomo': {
                'provider': 'matomo',
                'title': 'Matomo',
                'matomo_url': 'https://dummy-matomo.test/',
            },
            'siteimprove': None,
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

    forms = request.getfixturevalue('forms')
    create_new_organisation(
        app, 'Govikon', 'mails@govikon.ch', forms, create_files=False)

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
        username='member@example.org',
        password_hash=test_password,
        role='member'
    ))

    transaction.commit()
    close_all_sessions()

    return app


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(TownApp)
