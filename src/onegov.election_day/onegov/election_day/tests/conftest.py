import os.path
import pytest
import textwrap
import transaction

from onegov.core.crypto import hash_password
from onegov.election_day import ElectionDayApp
from onegov.user import User
from onegov.testing.utils import create_app


@pytest.fixture(scope='session')
def election_day_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


def create_election_day(request, canton="", municipality="", use_maps="false"):

    tmp = request.getfixturevalue('temporary_directory')

    app = create_app(ElectionDayApp, request, use_smtp=False)
    app.configuration['sms_directory'] = os.path.join(tmp, 'sms')
    app.configuration['d3_renderer'] = 'http://localhost:1337'
    app.session_manager.set_locale('de_CH', 'de_CH')

    app.filestorage.settext('principal.yml', textwrap.dedent("""
        name: Kanton Govikon
        logo: logo.jpg
        canton: {}
        municipality: {}
        use_maps: {}
        color: '#000'
        wabsti_import: true
    """.format(canton, municipality, use_maps)))

    app.session().add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('election_day_password'),
        role='admin'
    ))

    transaction.commit()

    return app


@pytest.fixture(scope="function")
def election_day_app(request):

    app = create_election_day(request, "zg")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_gr(request):

    app = create_election_day(request, "gr")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_sg(request):

    app = create_election_day(request, "sg")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_bern(request):

    app = create_election_day(request, "", "'351'", "true")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_kriens(request):

    app = create_election_day(request, "", "'1059'", "false")
    yield app
    app.session_manager.dispose()
