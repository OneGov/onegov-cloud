from __future__ import annotations

import pytest

from onegov.agency.app import AgencyApp
from onegov.agency.initial_content import create_new_organisation
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.user import User
from os import path
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client
from tests.shared.utils import create_app
from transaction import commit
from yaml import dump


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.orm import SessionManager


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
                'path': '/agency/*',
                'application': 'onegov.agency.app.AgencyApp',
                'namespace': 'agency',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true'
                    },
                    'websockets': {
                        'client_url': 'ws://localhost:8766',
                        'manage_url': 'ws://localhost:8766',
                        'manage_token': 'super-super-secret-token'
                    }
                }
            }
        ]
    }

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


def create_agency_app(
    request: pytest.FixtureRequest,
    enable_search: bool = False
) -> AgencyApp:

    app = create_app(
        AgencyApp,
        request,
        use_maildir=True,
        enable_search=enable_search,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    org = create_new_organisation(app, name="Govikon")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    session = app.session()
    test_password = request.getfixturevalue('test_password')
    session.add(
        User(
            username='admin@example.org',
            password_hash=test_password,
            role='admin'
        )
    )
    session.add(
        User(
            username='editor@example.org',
            password_hash=test_password,
            role='editor'
        )
    )
    session.add(
        User(
            username='member@example.org',
            password_hash=test_password,
            role='member'
        )
    )

    commit()
    close_all_sessions()
    return app


@pytest.fixture(scope='function')
def agency_app(request: pytest.FixtureRequest) -> Iterator[AgencyApp]:
    app = create_agency_app(request, enable_search=False)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def fts_agency_app(request: pytest.FixtureRequest) -> Iterator[AgencyApp]:
    app = create_agency_app(request, enable_search=True)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def client(agency_app: AgencyApp) -> Client[AgencyApp]:
    client = Client(agency_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@pytest.fixture(scope='function')
def client_with_fts(fts_agency_app: AgencyApp) -> Client[AgencyApp]:
    client = Client(fts_agency_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(AgencyApp)
