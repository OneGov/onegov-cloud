from onegov.core import Framework
from onegov.websockets import WebsocketsApp
from os import path
from pytest import fixture
from tests.shared.client import Client
from tests.shared.utils import create_app
from yaml import dump


class App(Framework, WebsocketsApp):
    pass


@fixture(scope='function')
def app(request):
    websockets = {
        'client_url': 'ws://localhost:8765',
        'manage_url': 'ws://localhost:8765',
        'manage_token': 'super-super-secret-token'
    }
    app = create_app(App, request, use_maildir=False, websockets=websockets)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(app):
    yield Client(app)


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'tests.onegov.websockets.conftest.App',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'websockets': {
                        'client_url': 'ws://localhost:8765',
                        'manage_url': 'ws://localhost:8765',
                        'manage_token': 'super-super-secret-token'
                    }
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path
