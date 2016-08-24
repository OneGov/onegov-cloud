import morepath
import onegov.core
import onegov.org
import pytest
import tempfile
import transaction
import shutil

from onegov.core.utils import Bunch, scan_morepath_modules
from onegov.org.models import Organisation
from onegov.org.initial_content import (
    add_initial_content, builtin_form_definitions)
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
    yield list(builtin_form_definitions())


@pytest.yield_fixture(scope='function')
def org_app(postgres_dsn, filestorage, test_password, smtp, forms):
    yield new_org_app(
        postgres_dsn, filestorage, test_password, smtp, forms)


@pytest.yield_fixture(scope='function')
def es_org_app(postgres_dsn, filestorage, test_password, smtp, es_url, forms):
    yield new_org_app(
        postgres_dsn, filestorage, test_password, smtp, forms, es_url)


def new_org_app(postgres_dsn, filestorage, test_password, smtp,
                forms, es_url=None):

    scan_morepath_modules(onegov.org.OrgApp)
    morepath.commit(onegov.org.OrgApp)

    app = onegov.org.OrgApp()
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
    add_initial_content(
        app.libres_registry,
        app.session_manager,
        'Govikon',
        forms
    )

    # cronjobs leave lingering sessions open, in real life this is not a
    # problem, but in testing it leads to connection pool exhaustion
    app.settings.cronjobs = Bunch(enabled=False)

    app.mail_host, app.mail_port = smtp.address
    app.mail_sender = 'mails@govikon.ch'
    app.mail_force_tls = False
    app.mail_username = None
    app.mail_password = None
    app.mail_use_directory = False
    app.smtp = smtp

    session = app.session()
    org = session.query(Organisation).one()
    org.meta['reply_to'] = 'mails@govikon.ch'

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
