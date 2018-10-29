from onegov_testing.utils import create_app
from onegov.core import Framework
from onegov.file import DepotApp
from os import path
from pytest import fixture
from yaml import dump


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foo',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


class TestApp(Framework, DepotApp):
    pass


@fixture(scope='function')
def test_app(request):
    app = create_app(TestApp, request, use_smtp=False)
    yield app
    app.session_manager.dispose()
