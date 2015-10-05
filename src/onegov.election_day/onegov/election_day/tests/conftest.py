import onegov.core
import onegov.election_day
import os.path
import pytest
import textwrap
import transaction

from morepath import setup
from onegov.core.crypto import hash_password
from onegov.testing.utils import scan_morepath_modules
from onegov.user import User
from uuid import uuid4


@pytest.fixture(scope='session')
def election_day_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


@pytest.yield_fixture(scope="function")
def election_day_app(postgres_dsn, temporary_directory, election_day_password):

    config = setup()
    scan_morepath_modules(onegov.election_day.ElectionDayApp, config)
    config.commit()

    app = onegov.election_day.ElectionDayApp()
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

    app.filestorage.setcontents('principal.yml', textwrap.dedent("""
        name: Kanton Govikon
        logo: logo.jpg
        canton: zg
        color: '#000'
    """))

    app.session().add(User(
        username='admin@example.org',
        password_hash=election_day_password,
        role='admin'
    ))

    transaction.commit()

    yield app
