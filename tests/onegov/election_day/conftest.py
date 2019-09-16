import os.path
import re
import tarfile
from collections import OrderedDict
from io import BytesIO

import pytest
import textwrap
import transaction

from onegov.ballot import Election, ElectionCompound, Vote, ProporzElection
from datetime import date
from onegov.core.crypto import hash_password
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.formats import import_election_internal_majorz, \
    import_election_internal_proporz
from tests.onegov.election_day.common import DummyRequest, print_errors, \
    get_tar_file_path, create_principal
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


def import_elections_internal(
        election_type,
        principal,
        domain,
        session,
        number_of_mandates,
        date_):
    """ Import test datasets in internal formats. For one election, there is
    a single file to load, so subfolders are not necessary.
    """
    assert isinstance(principal, str)

    model_mapping = dict(proporz=ProporzElection, majorz=Election)

    function_mapping = dict(
        proporz=import_election_internal_proporz,
        majorz=import_election_internal_majorz)

    api = 'internal'
    mimetype = 'text/plain'

    loaded_elections = OrderedDict()

    tar_fp = get_tar_file_path(
        domain, principal, api, 'election', election_type)
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            print(f'reading {name}.csv ...')

            if not date_:
                year = re.search(r'(\d){4}', name).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_

            csv_file = f.extractfile(member).read()
            election = model_mapping[election_type](
                title=f'election-{election_type}_{api}_{name}',
                date=election_date,
                number_of_mandates=number_of_mandates,
                domain=domain,
                type=election_type
            )
            principal_obj = create_principal(principal)
            session.add(election)
            session.flush()
            errors = function_mapping[election_type](
                election, principal_obj, BytesIO(csv_file), mimetype,
            )
            print_errors(errors)
            assert not errors
            loaded_elections[election.title] = election
    return loaded_elections


@pytest.fixture(scope="function")
def import_test_elections():
    return import_elections_internal


@pytest.fixture(scope="function")
def import_test_datasets(session):

    models = ('election', 'vote')
    election_types = ('majorz', 'proporz')
    apis = ('internal', 'wabstic', 'wabsti')
    domains = ('canton', 'region', 'municipality')

    def _import_test_datasets(
            api_format,
            model,
            principal,
            domain,
            election_type=None,
            number_of_mandates=None,
            date_=None):

        assert principal, 'Define a single principal'
        assert api_format in apis, 'apis not defined or not in available apis'
        assert model in models, 'Model not defined or not in available models'
        assert domain in domains, f'Possible domains: {domains}'
        if election_type:
            assert election_type in election_types

        all_loaded = OrderedDict()

        if model == 'election' and api_format == 'internal':
            assert election_type
            elections = import_elections_internal(
                election_type,
                principal,
                domain,
                session,
                number_of_mandates,
                date_
            )
            all_loaded.update(elections)
        else:
            raise NotImplementedError
        return all_loaded

    return _import_test_datasets

