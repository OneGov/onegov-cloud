import more.webassets
import onegov.core
import onegov.town
import os.path
import pytest
import transaction

from morepath import setup
from onegov.core.crypto import hash_password
from onegov.town.initial_content import add_initial_content
from onegov.user import User
from uuid import uuid4


@pytest.fixture(scope='session')
def town_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


@pytest.yield_fixture(scope="function")
def town_app(postgres_dsn, temporary_directory, town_password):

    config = setup()
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    app = onegov.town.TownApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': os.path.join(temporary_directory, 'file-storage'),
            'create': True
        },
        identity_secure=False,
        disable_memcached=True
    )
    app.set_application_id(app.namespace + '/' + 'test')

    session = app.session()
    add_initial_content(session, 'Govikon')

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

    yield app
