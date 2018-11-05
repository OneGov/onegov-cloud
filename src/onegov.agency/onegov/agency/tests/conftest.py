from onegov_testing.utils import create_app
from onegov.agency.app import AgencyApp
from os import path
from pytest import fixture
from yaml import dump


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/foo/*',
                'application': 'onegov.agency.app.AgencyApp',
                'namespace': 'foo',
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
                }
            }
        ]
    }

    session_manager.ensure_schema_exists('foo-bar')

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


@fixture(scope='function')
def agency_app(request):
    app = create_app(AgencyApp, request, use_smtp=False)
    yield app
    app.session_manager.dispose()
