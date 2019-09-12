import os.path
import pytest
import textwrap
import transaction
from onegov.ballot import Election, ElectionCompound, Vote
from datetime import date
from onegov.core.crypto import hash_password
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import SearchableArchivedResultCollection
from tests.onegov.election_day.common import DummyRequest
from onegov.user import User
from tests.shared.utils import create_app


@pytest.fixture(scope='session')
def election_day_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


def create_election_day(request, canton='', municipality='', use_maps='false'):

    tmp = request.getfixturevalue('temporary_directory')

    app = create_app(ElectionDayApp, request, use_smtp=True)
    app.configuration['sms_directory'] = os.path.join(tmp, 'sms')
    app.configuration['d3_renderer'] = 'http://localhost:1337'
    app.session_manager.set_locale('de_CH', 'de_CH')

    app.filestorage.settext('principal.yml', textwrap.dedent("""
        name: Kanton Govikon
        logo: logo.jpg
        {}
        use_maps: {}
        color: '#000'
        wabsti_import: true
    """.format(
        (
            'canton: {}'.format(canton) if canton else
            'municipality: {}'.format(municipality)
        ),
        use_maps
    )))

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


@pytest.fixture(scope='function')
def related_link_labels():
    return {'de_CH': 'DE', 'fr_CH': 'FR', 'it_CH': 'IT', 'rm_CH': 'RM'}


@pytest.fixture(scope='function')
def searchable_archive(session):
    archive = SearchableArchivedResultCollection(session)

    # Create 12 entries
    for year in (2009, 2011, 2014):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for year in (2008, 2012, 2016):
        session.add(
            ElectionCompound(
                title="Elections {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for year in (2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )
    for domain in ('canton', 'region', 'municipality'):
        session.add(
            Election(
                title="Election {}".format(domain),
                domain=domain,
                date=date(2019, 1, 1),
            )
        )

    session.flush()
    archive.update_all(DummyRequest())
    return archive
