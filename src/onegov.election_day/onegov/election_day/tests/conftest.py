import morepath
import onegov.core
import onegov.election_day
import os.path
import pytest
import textwrap
import transaction

from onegov.core.crypto import hash_password
from onegov.core.utils import scan_morepath_modules
from onegov.user import User
from uuid import uuid4


@pytest.fixture(scope='session')
def election_day_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


def create_app(postgres_dsn, temporary_directory, election_day_password,
               canton="", municipality="", use_maps="false"):

    scan_morepath_modules(onegov.election_day.ElectionDayApp)
    morepath.commit(onegov.election_day.ElectionDayApp)

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
        disable_memcached=True,
        sms_directory=os.path.join(temporary_directory, 'sms'),
    )
    app.set_application_id(app.namespace + '/' + 'test')

    app.filestorage.settext('principal.yml', textwrap.dedent("""
        name: Kanton Govikon
        logo: logo.jpg
        canton: {}
        municipality: {}
        use_maps: {}
        color: '#000'
    """.format(canton, municipality, use_maps)))

    app.session().add(User(
        username='admin@example.org',
        password_hash=election_day_password,
        role='admin'
    ))

    transaction.commit()

    return app


@pytest.yield_fixture(scope="function")
def election_day_app(postgres_dsn, temporary_directory, election_day_password):

    yield create_app(
        postgres_dsn, temporary_directory, election_day_password, "zg"
    )


@pytest.yield_fixture(scope="function")
def election_day_app_gr(postgres_dsn, temporary_directory,
                        election_day_password):

    yield create_app(
        postgres_dsn, temporary_directory, election_day_password, "gr"
    )


@pytest.yield_fixture(scope="function")
def election_day_app_sg(postgres_dsn, temporary_directory,
                        election_day_password):

    yield create_app(
        postgres_dsn, temporary_directory, election_day_password, "sg"
    )


@pytest.yield_fixture(scope="function")
def election_day_app_bern(postgres_dsn, temporary_directory,
                          election_day_password):

    yield create_app(
        postgres_dsn, temporary_directory, election_day_password, "",
        "'351'", "true"
    )


@pytest.yield_fixture(scope="function")
def election_day_app_kriens(postgres_dsn, temporary_directory,
                            election_day_password):

    yield create_app(
        postgres_dsn, temporary_directory, election_day_password, "",
        "'1059'", "false"
    )
