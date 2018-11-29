from onegov_testing import Client
from onegov_testing.utils import create_app
from onegov.agency.app import AgencyApp
from onegov.agency.initial_content import create_new_organisation
from onegov.user import User
from os import path
from pytest import fixture
from transaction import commit
from yaml import dump


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
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
                }
            }
        ]
    }

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


@fixture(scope='function')
def agency_app(request):
    app = create_app(AgencyApp, request, use_smtp=True)
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

    commit()
    session.close_all()

    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(agency_app):
    client = Client(agency_app)
    client.skip_first_form = True
    client.use_intercooler = True
    return client
