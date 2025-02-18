
from onegov.core.orm.observer import ScopedPropertyObserver
from os import path
from yaml import dump

from onegov.core.utils import module_path
from onegov.pas.app import PasApp
from onegov.pas.content.initial import create_new_organisation
from onegov.user import User
from pytest import fixture
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client
from tests.shared.utils import create_app
from transaction import commit


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/pas/*',
                'application': 'onegov.pas.app.PasApp',
                'namespace': 'pas',
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


def create_pas_app(request, use_elasticsearch=False):
    app = create_app(
        PasApp,
        request,
        use_maildir=True,
        use_elasticsearch=use_elasticsearch,
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


@fixture(scope='function')
def pas_app(request):
    app = create_pas_app(request, use_elasticsearch=False)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def es_pas_app(request):
    app = create_pas_app(request, use_elasticsearch=True)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(pas_app):
    client = Client(pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@fixture(scope='function')
def client_with_es(es_pas_app):
    client = Client(es_pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@fixture(scope="session", autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(PasApp)


@fixture(params=['csv', 'xlsx'])
def commission_test_files(request):
    """Yield both CSV and XLSX test files one at a time."""
    file_type = request.param
    filename = f'commission_test.{file_type}'

    # Get the file path using module_path
    file_path = module_path('tests.onegov.pas', f'/fixtures/{filename}')

    # Read the file content based on type
    if file_type == 'csv':
        with open(file_path, 'r') as f:
            content = f.read()
    else:  # xlsx
        with open(file_path, 'rb') as f:
            content = f.read()

    yield {
        'path': file_path,
        'content': content,
        'type': file_type
    }
