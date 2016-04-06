import morepath
import onegov.core
import onegov.town
import pytest
import tempfile
import transaction
import shutil

from onegov.core.crypto import hash_password
from onegov.core.utils import Bunch, scan_morepath_modules
from onegov.town.initial_content import (
    add_initial_content, builtin_form_definitions
)
from onegov.town.models import Town
from onegov.user import User
from uuid import uuid4


@pytest.yield_fixture(scope='session')
def handlers():
    yield onegov.ticket.handlers
    onegov.ticket.handlers.registry = {}


@pytest.fixture(scope='session')
def town_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


@pytest.yield_fixture(scope='session')
def filestorage():
    directory = tempfile.mkdtemp()
    yield directory
    shutil.rmtree(directory)


@pytest.yield_fixture(scope='session')
def form_definitions():
    yield list(builtin_form_definitions())


@pytest.yield_fixture(scope='function')
def town_app(postgres_dsn, filestorage, town_password, smtp,
             form_definitions):
    yield new_town_app(
        postgres_dsn, filestorage, town_password, smtp, form_definitions
    )


@pytest.yield_fixture(scope='function')
def es_town_app(postgres_dsn, filestorage, town_password, smtp,
                form_definitions, es_url):
    yield new_town_app(
        postgres_dsn, filestorage, town_password, smtp, form_definitions,
        es_url
    )


def new_town_app(postgres_dsn, filestorage, town_password, smtp,
                 form_definitions, es_url=None):

    scan_morepath_modules(onegov.town.TownApp)
    morepath.commit(onegov.town.TownApp)

    app = onegov.town.TownApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': filestorage,
            'create': True
        },
        identity_secure=False,
        disable_memcached=True,
        enable_elasticsearch=es_url and True or False,
        elasticsearch_hosts=[es_url]
    )
    app.set_application_id(app.namespace + '/' + 'test')
    add_initial_content(
        app.libres_registry,
        app.session_manager,
        'Govikon',
        form_definitions
    )

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    session = app.session()

    town = session.query(Town).one()
    town.meta['reply_to'] = 'mails@govikon.ch'

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
        password_hash=town_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=town_password,
        role='editor'
    ))

    transaction.commit()
    session.close_all()

    return app
