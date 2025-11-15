from __future__ import annotations

import transaction
import pytest

from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.feriennet import FeriennetApp
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.models import VacationActivity
from onegov.user import User, UserCollection
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Session
    from tests.onegov.activity.conftest import Scenario as BaseScenario
    from tests.shared.browser import ExtendedBrowser

    _AppT = TypeVar(
        '_AppT',
        bound=FeriennetApp,
        default='TestApp',
        covariant=True
    )
    Scenario = BaseScenario[VacationActivity]
else:
    from tests.onegov.activity.conftest import Scenario

    _AppT = TypeVar('_AppT', bound=FeriennetApp)


class TestApp(FeriennetApp):
    __test__ = False
    maildir: str


class Client(BaseClient[_AppT]):
    skip_n_forms = 1
    use_intercooler = True

    def fill_out_profile(
        self,
        first_name: str = 'Scrooge',
        last_name: str = 'McDuck'
    ) -> None:

        profile = self.get('/userprofile')
        profile.form['salutation'] = 'mr'
        profile.form['first_name'] = first_name
        profile.form['last_name'] = last_name
        profile.form['address'] = 'foobar'
        profile.form['zip_code'] = '1234'
        profile.form['place'] = 'Duckburg'
        profile.form['emergency'] = f'0123 456 789 ({first_name} {last_name})'
        if 'political_municipality' in profile.form.fields:
            profile.form['political_municipality'] = 'Bruckerburg'

        profile.form.submit()


@pytest.fixture(scope='function')
def client(feriennet_app: TestApp) -> Client[TestApp]:
    return Client(feriennet_app)


@pytest.fixture(scope='function')
def client_with_fts(fts_feriennet_app: TestApp) -> Client[TestApp]:
    return Client(fts_feriennet_app)


@pytest.fixture(scope='function')
def feriennet_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_feriennet_app(request, enable_search=False)


@pytest.fixture(scope='function')
def fts_feriennet_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_feriennet_app(request, enable_search=True)


@pytest.fixture(scope='function')
def browser(
    browser: ExtendedBrowser,
    feriennet_app_url: str
) -> Iterator[ExtendedBrowser]:

    browser.baseurl = feriennet_app_url
    yield browser


@pytest.fixture(scope='function')
def feriennet_app_url(
    request: pytest.FixtureRequest,
    feriennet_app: TestApp
) -> Iterator[str]:

    feriennet_app.print_exceptions = True
    server = WSGIServer(application=feriennet_app)
    server.start()
    yield server.url
    server.stop()


def create_feriennet_app(
    request: pytest.FixtureRequest,
    enable_search: bool
) -> TestApp:

    app = create_app(
        app_class=TestApp,
        request=request,
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

    org = create_new_organisation(app, name="Govikon", create_files=False)
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.
    test_password = request.getfixturevalue('test_password')

    session.add(User(
        username='admin@example.org',
        realname='Foo Bar',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        realname='Boo Far',
        password_hash=test_password,
        role='editor'
    ))

    transaction.commit()
    close_all_sessions()

    return app


@pytest.fixture(scope='function')
def scenario(
    request: pytest.FixtureRequest,
    session: Session,
    test_password: str
) -> Scenario:
    for name in request.fixturenames:
        if name in ('feriennet_app', 'fts_feriennet_app'):
            session = request.getfixturevalue(name).session()

    return Scenario(session, test_password, activity_model=VacationActivity)


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(FeriennetApp)


@pytest.fixture(scope='function')
def owner(session: Session) -> User:
    return UserCollection(session).add(
        username='owner@example.org',
        password='hunter2',
        role='editor'
    )
