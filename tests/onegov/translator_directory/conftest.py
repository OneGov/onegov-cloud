from __future__ import annotations

import pytest
import transaction

from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.initial_content import create_new_organisation
from onegov.user import User
from os import path
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client as BaseClient
from tests.shared.utils import create_app
from onegov.core.crypto import hash_password
from yaml import dump


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.orm import SessionManager
    from tests.shared.client import ExtendedResponse

    _AppT = TypeVar(
        '_AppT',
        bound=TranslatorDirectoryApp,
        default='TestApp',
        covariant=True
    )
else:
    _AppT = TypeVar('_AppT', bound=TranslatorDirectoryApp)


class TestApp(TranslatorDirectoryApp):
    __test__ = False
    maildir: str


class Client(BaseClient[_AppT]):

    use_intercooler = True
    skip_n_forms = 1

    def login_member(self, to: str | None = None) -> ExtendedResponse:
        return self.login('member@example.org', 'hunter2', to)

    def login_translator(self, to: str | None = None) -> ExtendedResponse:
        return self.login('translator@example.org', 'hunter2', to)


@pytest.fixture(scope='function')
def translator_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_translator_app(request, False)


@pytest.fixture(scope='function')
def fts_translator_app(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    yield create_translator_app(request, True)


@pytest.fixture(scope='function')
def client(translator_app: TestApp) -> Client[TestApp]:
    return Client(translator_app)


@pytest.fixture(scope='function')
def client_with_fts(fts_translator_app: TestApp) -> Client[TestApp]:
    return Client(fts_translator_app)


def create_translator_app(
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

    org = create_new_organisation(app, name="Übersetzerverzeichnis")
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.

    session.add(User(
        username='admin@example.org',
        password_hash=hash_password('hunter2'),
        role='admin',
        realname='John Doe',
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=hash_password('hunter2'),
        role='editor'
    ))

    session.add(User(
        username='member@example.org',
        password_hash=hash_password('hunter2'),
        role='member'
    ))

    session.add(User(
        username='translator@example.org',
        password_hash=hash_password('hunter2'),
        role='translator'
    ))

    transaction.commit()
    close_all_sessions()

    return app


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
                'path': '/translator_directory/*',
                'application': 'onegov.translator_directory.'
                               'TranslatorDirectoryApp',
                'namespace': 'translator_directory',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    # FIXME: For some reason some of the tests crash on the CI
                    #        under certain circumstances, if we try to
                    #        configure an indexer, eventually we should try
                    #        to get rid of this hack
                    'enable_elasticsearch': False,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'true',
                    },
                    'websockets': {
                        'client_url': 'ws://localhost:8766',
                        'manage_url': 'ws://localhost:8766',
                        'manage_token': 'super-super-secret-token',
                    },
                },
            }
        ]
    }

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(TranslatorDirectoryApp)
