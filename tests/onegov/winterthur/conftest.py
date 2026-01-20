from __future__ import annotations

import pytest
import transaction

from onegov.core.csv import CSVFile
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.core.utils import module_path
from onegov.user import User
from onegov.winterthur import WinterthurApp
from onegov.winterthur.initial_content import create_new_organisation
from pathlib import Path
from sqlalchemy.orm.session import close_all_sessions
from tests.shared.utils import create_app
from tests.shared import Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


class TestApp(WinterthurApp):
    __test__ = False
    maildir: str


@pytest.fixture()
def fixtures() -> Path:
    return Path(module_path('tests.onegov.winterthur', 'fixtures'))


@pytest.fixture()
def streets_csv(fixtures: Path) -> Iterator[CSVFile]:
    with (fixtures / 'streets.csv').open('rb') as f:
        yield CSVFile(f)


@pytest.fixture()
def addresses_csv(fixtures: Path) -> Iterator[CSVFile]:
    with (fixtures / 'addresses.csv').open('rb') as f:
        yield CSVFile(f)


@pytest.fixture(scope='function')
def winterthur_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_winterthur_app(request, enable_search=False)


@pytest.fixture(scope='function')
def fts_winterthur_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_winterthur_app(request, enable_search=True)


def create_winterthur_app(
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

    session = app.session()

    org = create_new_organisation(app, name="Winterthur")
    org.meta['reply_to'] = 'mails@govikon.ch'
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

    transaction.commit()
    close_all_sessions()

    return app


@pytest.fixture(scope='function')
def client(winterthur_app: TestApp) -> Client[TestApp]:
    client = Client(winterthur_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@pytest.fixture(scope='function')
def client_with_fts(fts_winterthur_app: TestApp) -> Client[TestApp]:
    client = Client(fts_winterthur_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(WinterthurApp)
