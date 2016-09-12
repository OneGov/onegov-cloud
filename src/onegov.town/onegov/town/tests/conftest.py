import onegov.core
import onegov.town
import pytest
import tempfile
import transaction
import shutil

from onegov.core.utils import Bunch, module_path, scan_morepath_modules
from onegov.town.initial_content import (
    create_new_organisation, builtin_form_definitions)
from onegov.user import User
from uuid import uuid4


@pytest.yield_fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.yield_fixture(scope='session')
def filestorage():
    directory = tempfile.mkdtemp()
    yield directory
    shutil.rmtree(directory)


@pytest.yield_fixture(scope='session')
def forms():
    yield list(builtin_form_definitions(
        module_path('onegov.town', 'forms/builtin')))


@pytest.yield_fixture(scope='function')
def town_app(postgres_dsn, filestorage, test_password, smtp, forms):
    yield new_town_app(postgres_dsn, filestorage, test_password, smtp, forms)


@pytest.yield_fixture(scope='function')
def es_town_app(postgres_dsn, filestorage, test_password, smtp, forms, es_url):
    yield new_town_app(
        postgres_dsn, filestorage, test_password, smtp, forms, es_url)


def new_town_app(postgres_dsn, filestorage, test_password, smtp,
                 forms, es_url=None):

    scan_morepath_modules(onegov.town.TownApp)
    onegov.town.TownApp.commit()

    app = onegov.town.TownApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': filestorage,
            'create': True
        },
        depot_backend='depot.io.memory.MemoryFileStorage',
        identity_secure=False,
        disable_memcached=True,
        enable_elasticsearch=es_url and True or False,
        elasticsearch_hosts=[es_url]
    )
    app.set_application_id(app.namespace + '/' + 'test')
    app.bind_depot()

    create_new_organisation(app, 'Govikon', 'mails@govikon.ch', forms)

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    session = app.session()

    app.mail_host, app.mail_port = smtp.address
    app.mail_sender = 'mails@govikon.ch'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False
    app.smtp = smtp

    # usually we don't want to create the users directly, anywhere else you
    # *need* to go through the UserCollection. Here however, we can improve
    # the test speed by not hashing the password for every test.

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
    session.close_all()

    return app
