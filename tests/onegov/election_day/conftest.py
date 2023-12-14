import os.path
import pytest
import re
import tarfile
import textwrap
import transaction
from collections import OrderedDict
from datetime import date
from io import BytesIO
from onegov.ballot import (
    Election, Vote, ProporzElection, ComplexVote, ElectionCompound)
from onegov.core.crypto import hash_password
from onegov.election_day import ElectionDayApp
from onegov.election_day.hidden_by_principal import (
    always_hide_candidate_by_entity_chart_percentages as hide_chart_perc,
    hide_connections_chart_intermediate_results as hide_conn_chart,
    hide_candidates_chart_intermediate_results as hide_cand_chart)
from onegov.election_day.formats import (
    import_election_internal_majorz, import_election_internal_proporz,
    import_election_wabstic_proporz, import_election_wabstic_majorz,
    import_election_wabsti_proporz, import_election_wabsti_majorz,
    import_vote_internal, import_vote_wabsti, import_party_results_internal,
    import_election_compound_internal)
from tests.onegov.election_day.common import (
    print_errors, get_tar_file_path, create_principal)
from onegov.pdf import Pdf
from onegov.user import User
from tests.shared.utils import create_app


def bool_as_string(val):
    assert isinstance(val, bool)
    return 'true' if val else 'false'


@pytest.fixture(scope='session')
def election_day_password():
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


def create_election_day(
    request,
    canton='',
    canton_name='',
    municipality='',
    use_maps='false',
    hide_candidate_chart_percentages=hide_chart_perc,
    hide_connections_chart=hide_conn_chart,
    hide_candidates_chart=hide_cand_chart,
):
    tmp = request.getfixturevalue('temporary_directory')

    websockets = {
        'client_url': 'ws://localhost:8766',
        'manage_url': 'ws://localhost:8766',
        'manage_token': 'super-super-secret-token'
    }
    app = create_app(
        ElectionDayApp, request, use_maildir=True, websockets=websockets
    )
    app.sms_directory = os.path.join(tmp, 'sms')
    app.configuration['d3_renderer'] = 'http://localhost:1337'
    app.session_manager.set_locale('de_CH', 'de_CH')
    municipality = f'municipality: {municipality}' if municipality else ''
    chart_percentages = bool_as_string(hide_candidate_chart_percentages)

    app.filestorage.writetext('principal.yml', textwrap.dedent(f"""
        name: Kanton Govikon
        logo: logo.jpg
        canton: {canton}
        canton_name: {canton_name}
        {municipality}
        use_maps: {use_maps}
        color: '#000'
        wabsti_import: true
        hidden_elements:
          always:
            candidate-by-entity:
              chart_percentages: {chart_percentages}
          intermediate_results:
            connections:
              chart: {bool_as_string(hide_connections_chart)}
            candidates:
              chart: {bool_as_string(hide_candidates_chart)}
          tabs:
            elections:
              - lists
    """))

    app.session().add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('election_day_password'),
        role='admin'
    ))

    transaction.commit()

    return app


@pytest.fixture(scope="function")
def election_day_app_bl(request):
    app = create_election_day(request, canton="bl")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_zg(request):
    app = create_election_day(
        request,
        canton="zg",
        hide_candidate_chart_percentages=True)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_gr(request):
    app = create_election_day(request, canton="gr")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_sg(request):
    app = create_election_day(
        request,
        canton="sg",
        hide_candidates_chart=True,
        hide_connections_chart=True
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_sz(request):
    app = create_election_day(
        request,
        canton="sz",
        hide_candidates_chart=True,
        hide_connections_chart=True
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_bern(request):
    app = create_election_day(
        request,
        canton="be",
        canton_name="Kanton Bern",
        municipality="'351'",
        use_maps="true"
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_kriens(request):
    app = create_election_day(
        request,
        canton="lu",
        canton_name="Kanton Luzern",
        municipality="'1059'",
        use_maps="false"
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def related_link_labels():
    return {'de_CH': 'DE', 'fr_CH': 'FR', 'it_CH': 'IT', 'rm_CH': 'RM'}


def import_elections_internal(
    election_type,
    principal,
    domain,
    session,
    number_of_mandates,
    date_,
    domain_segment,
    dataset_name,
    has_expats,
    election,
    municipality
):
    """
    Import test datasets in internal formats. For one election, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    if dataset_name:
        assert '.' not in dataset_name, 'Remove the file ending'\
                                        ' from dataset_name'

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
            if dataset_name and dataset_name != name:
                continue
            print(f'reading {name}.csv ...')

            if not date_:
                year = re.search(r'(\d){4}', name).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_

            csv_file = f.extractfile(member).read()
            if not election:
                election = model_mapping[election_type](
                    title=f'{election_type}_{api}_{name}',
                    date=election_date,
                    number_of_mandates=number_of_mandates,
                    domain=domain,
                    domain_segment=domain_segment,
                    type=election_type,
                    has_expats=has_expats,
                )
            principal_obj = create_principal(principal, municipality)
            session.add(election)
            session.flush()
            errors = function_mapping[election_type](
                election, principal_obj, BytesIO(csv_file), mimetype,
            )
            loaded_elections[election.title] = (election, errors)
    print(tar_fp)
    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def import_election_compounds_internal(
    principal,
    domain,
    session,
    number_of_mandates,
    date_,
    domain_segment,
    domain_supersegment,
    dataset_name,
    has_expats,
    election,
    municipality
):
    """
    Import test datasets in internal formats. For one election, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    assert isinstance(domain_segment, (tuple, list))
    assert isinstance(domain_supersegment, (tuple, list))
    assert isinstance(number_of_mandates, (tuple, list))
    assert len(domain_segment) == len(number_of_mandates)
    assert len(domain_supersegment) == len(number_of_mandates)
    if dataset_name:
        assert '.' not in dataset_name, 'Remove the file ending'\
                                        ' from dataset_name'

    api = 'internal'
    mimetype = 'text/plain'

    loaded_elections = OrderedDict()

    tar_fp = get_tar_file_path(domain, principal, api, 'election', 'proporz')
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            if dataset_name and dataset_name != name:
                continue
            print(f'reading {name}.csv ...')

            if not date_:
                year = re.search(r'(\d){4}', name).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_

            elections = []
            if not election:
                election = ElectionCompound(
                    title=f'compound_{api}_{name}',
                    date=election_date,
                    domain='canton',
                )
                for index in range(len(domain_segment)):
                    proporz_election = ProporzElection(
                        title=f'proporz_{api}_{domain_segment[index]}',
                        date=election_date,
                        shortcode=f'{index}',
                        number_of_mandates=number_of_mandates[index],
                        domain=domain,
                        domain_segment=domain_segment[index],
                        domain_supersegment=domain_supersegment[index],
                        has_expats=has_expats,
                    )
                    elections.append(proporz_election)
                    session.add(proporz_election)

            session.add(election)
            session.flush()

            election.elections = elections if elections else election.elections
            assert election.number_of_mandates == sum(number_of_mandates)

            principal_obj = create_principal(principal, municipality)
            csv_file = f.extractfile(member).read()
            errors = import_election_compound_internal(
                election, principal_obj, BytesIO(csv_file), mimetype,
            )
            loaded_elections[election.title] = (election, errors)

    print(tar_fp)

    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def import_parties_internal(
    principal,
    domain,
    dataset_name,
    election,
):
    """
    Import test datasets with party results in internal formats. For one
    election, there is a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    if dataset_name:
        assert '.' not in dataset_name, 'Remove the file ending'\
                                        ' from dataset_name'

    tar_fp = get_tar_file_path(
        domain, principal, 'internal', 'election', 'proporz'
    )
    with tarfile.open(tar_fp, 'r:gz') as f:
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]
        for name, member in zip(names, members):
            if name == dataset_name:
                file = f.extractfile(member).read()
                principal_obj = create_principal(principal)
                errors = import_party_results_internal(
                    election, principal_obj, BytesIO(file), 'text/plain',
                    ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
                )
                break
        else:
            errors = ['Dataset not found']

    return errors


def import_elections_wabstic(
    election_type,
    principal,
    domain,
    session,
    number_of_mandates,
    date_,
    domain_segment,
    number,
    district,
    dataset_name,
    has_expats,
    election,
    municipality
):
    """
    :param principal: canton as string, e.g. zg
    :param dataset_name: If set, import this dataset having that folder name
    """
    assert isinstance(principal, str)
    assert isinstance(number, str)

    model_mapping = dict(proporz=ProporzElection, majorz=Election)

    function_mapping = dict(
        proporz=import_election_wabstic_proporz,
        majorz=import_election_wabstic_majorz)

    api = 'wabstic'
    mimetype = 'text/plain'

    loaded_elections = OrderedDict()

    tar_fp = get_tar_file_path(
        domain, principal, api, 'election', election_type)
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering
        folders = set(fn.split('/')[0] for fn in f.getnames())

        for folder in folders:
            if dataset_name and dataset_name != folder:
                continue
            if not date_:
                year = re.search(r'(\d){4}', folder).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_
            if not election:
                election = model_mapping[election_type](
                    title=f'{election_type}_{api}_{folder}',
                    date=election_date,
                    number_of_mandates=number_of_mandates,
                    domain=domain,
                    domain_segment=domain_segment,
                    # type=election_type,
                    has_expats=has_expats
                )
            principal_obj = create_principal(principal, municipality)
            session.add(election)
            session.flush()

            files = [name.split('/')[1]
                     for name in f.getnames()
                     if name.startswith(folder)
                     and name != folder]

            files_input = {
                'file_' + name.split('.')[0].lower(): BytesIO(
                    f.extractfile(f'{folder}/{name}').read()) for name in files
            }
            mimetypes = {'mimetype_' + name.split('.')[0].lower(): mimetype
                         for name in files}

            errors = function_mapping[election_type](
                election,
                principal_obj,
                number=number,
                district=district,
                **files_input,
                **mimetypes
            )
            loaded_elections[election.title] = (election, errors)
    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def get_mimetype(archive_filename):
    fname = archive_filename.split('/')[-1]
    ending = fname.split('.')[-1]
    if ending.lower() in ('xlsx', 'xls'):
        return 'application/vnd.openxmlformats-'\
               'officedocument.spreadsheetml.sheet'
    else:
        return 'text/plain'


def import_elections_wabsti(
    election_type,
    principal,
    domain,
    session,
    number_of_mandates,
    date_,
    domain_segment,
    number,
    district,
    dataset_name,
    has_expats,
    election,
    municipality

):
    """
    :param principal: canton as string, e.g. zg
    :param dataset_name: If set, import this dataset having that folder name
    """
    assert isinstance(principal, str)
    assert isinstance(number, str)

    model_mapping = dict(proporz=ProporzElection, majorz=Election)

    api = 'wabsti'

    loaded_elections = OrderedDict()

    tar_fp = get_tar_file_path(
        domain, principal, api, 'election', election_type)
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering
        folders = set(fn.split('/')[0] for fn in f.getnames())

        for folder in folders:
            if dataset_name and dataset_name != folder:
                continue
            if not date_:
                year = re.search(r'(\d){4}', folder).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_
            if not election:
                election = model_mapping[election_type](
                    title=f'{election_type}_{api}_{folder}',
                    date=election_date,
                    number_of_mandates=number_of_mandates,
                    domain=domain,
                    domain_segment=domain_segment,
                    # type=election_type,
                    has_expats=has_expats
                )
            principal_obj = create_principal(principal, municipality)
            session.add(election)
            session.flush()

            files = [name.split('/')[1]
                     for name in f.getnames()
                     if name.startswith(folder)
                     and name != folder]
            assert files, f'No files found in {folder}'
            mimetype = get_mimetype(files[0])

            def find_and_read(
                files, keyword=None, no_keywords=None, folder=folder
            ):
                no_kw_results = []
                assert keyword or no_keywords
                for file in files:
                    if keyword:
                        if keyword.lower() in file.lower():
                            return BytesIO(
                                f.extractfile(f'{folder}/{file}').read())
                    elif all(
                            (kw.lower() not in file.lower()
                             for kw in no_keywords)):
                        no_kw_results.append(file)
                if no_keywords:
                    assert no_kw_results and len(no_kw_results) == 1
                    filename = f'{folder}/{no_kw_results[0]}'
                    return BytesIO(
                        f.extractfile(filename).read())
                return None

            file = find_and_read(files, no_keywords=[
                'statistik', 'kandidaten', 'verbindungen'])

            assert file, 'Main result file is None'

            additional_files = dict(
                connections_file=find_and_read(files, keyword='Verbindungen'),
                elected_file=find_and_read(files, keyword='Kandidaten'),
                statistics_file=find_and_read(files, keyword='Statistik')
            )
            if election_type == 'proporz':
                errors = import_election_wabsti_proporz(
                    election,
                    principal_obj,
                    file,
                    mimetype,
                    **additional_files,
                    connections_mimetype=mimetype,
                    elected_mimetype=mimetype,
                    statistics_mimetype=mimetype,

                )
            else:
                errors = import_election_wabsti_majorz(
                    election,
                    principal_obj,
                    file,
                    mimetype,
                    elected_file=additional_files['elected_file'],
                    elected_mimetype=mimetype
                )

            print_errors(errors)
            loaded_elections[election.title] = (election, errors)
    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def import_votes_internal(
    vote_type,
    principal,
    domain,
    session,
    date_,
    dataset_name,
    has_expats,
    vote,
    municipality
):
    """
    Import test datasets in internal formats. For one vote, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    assert '.' not in dataset_name, 'Remove file ending from dataset_name'

    api = 'internal'
    mimetype = 'text/plain'

    model_mapping = dict(simple=Vote, complex=ComplexVote)
    loaded_votes = OrderedDict()

    tar_fp = get_tar_file_path(
        domain, principal, api, 'vote', vote_type)
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering (zip..)
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            if dataset_name and dataset_name != name:
                continue
            print(f'reading {name}.csv ...')

            if not date_:
                year = re.search(r'(\d){4}', name).group(0)
                assert year, 'Put the a year into the filename'
                vote_date = date(int(year), 1, 1)
            else:
                vote_date = date_

            csv_file = f.extractfile(member).read()
            if not vote:
                vote = model_mapping[vote_type](
                    title=f'{vote_type}_{api}_{name}',
                    date=vote_date,
                    domain=domain,
                    has_expats=has_expats,
                )
            principal_obj = create_principal(principal, municipality)
            session.add(vote)
            session.flush()
            errors = import_vote_internal(
                vote, principal_obj, BytesIO(csv_file), mimetype,
            )
            loaded_votes[vote.title] = (vote, errors)
    print(tar_fp)
    assert loaded_votes, 'No vote was loaded'
    return loaded_votes


def import_votes_wabsti(
    vote_type,
    principal,
    domain,
    session,
    date_,
    dataset_name,
    has_expats,
    vote,
    vote_number,
    municipality
):
    assert isinstance(principal, str)

    api = 'wabsti'
    mimetype = 'text/plain'
    model_mapping = dict(simple=Vote, complex=ComplexVote)

    loaded_votes = OrderedDict()
    tar_fp = get_tar_file_path(
        domain, principal, api, 'vote', vote_type)

    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            if dataset_name and dataset_name != name:
                continue
            print(f'reading {name}.csv ...')

            if not date_ and not vote:
                year = re.search(r'(\d){4}', name).group(0)
                assert year, 'Put the a year into the filename'
                election_date = date(int(year), 1, 1)
            else:
                election_date = date_

            csv_file = f.extractfile(member).read()
            if not vote:
                vote = model_mapping[vote_type](
                    title=f'{vote_type}_{api}_{name}',
                    date=election_date,
                    domain=domain,
                    has_expats=has_expats,
                )
            principal_obj = create_principal(principal, municipality)
            session.add(vote)
            session.flush()
            errors = import_vote_wabsti(
                vote, principal_obj, vote_number, BytesIO(csv_file), mimetype)
            loaded_votes[vote.title] = (vote, errors)

    print(tar_fp)
    assert loaded_votes, 'No vote was loaded'
    return loaded_votes


@pytest.fixture(scope="function")
def import_test_datasets(session):

    models = ('election', 'vote', 'parties', 'election_compound')
    election_types = ('majorz', 'proporz')
    apis = ('internal', 'wabstic', 'wabsti')
    domains = (
        'federation', 'canton', 'region', 'district', 'municipality', 'none'
    )
    vote_types = ('simple', 'complex')

    def _import_test_datasets(
        api_format,
        model,
        principal,
        domain,
        election_type=None,
        number_of_mandates=None,
        date_=None,
        domain_segment='',
        domain_supersegment='',
        dataset_name=None,
        has_expats=False,
        election=None,
        election_number='1',
        election_district=None,
        municipality=None,
        vote_type='simple',
        vote=None,
        vote_number=1,
        app_session=None
    ):
        if not app_session:
            app_session = session

        assert domain in domains
        assert api_format in apis, 'apis not defined or not in available apis'
        assert principal, 'Define a single principal'
        assert model in models, 'Model not defined or not in available models'

        if not election:
            assert domain in domains, f'Possible domains: {domains}'
            if election_type:
                assert election_type in election_types

        if model == 'vote':
            assert vote_type in vote_types

        all_loaded = OrderedDict()
        if model == 'election':
            assert election_type, 'Election Type is needed to load fixture'
            if api_format == 'internal':
                elections = import_elections_internal(
                    election_type,
                    principal,
                    domain,
                    app_session,
                    number_of_mandates=number_of_mandates,
                    date_=date_,
                    domain_segment=domain_segment,
                    dataset_name=dataset_name,
                    has_expats=has_expats,
                    election=election,
                    municipality=municipality
                )
                all_loaded.update(elections)
            elif api_format == 'wabstic':
                elections = import_elections_wabstic(
                    election_type,
                    principal,
                    domain,
                    app_session,
                    number_of_mandates=number_of_mandates,
                    date_=date_,
                    domain_segment=domain_segment,
                    dataset_name=dataset_name,
                    has_expats=has_expats,
                    election=election,
                    number=election_number,
                    district=election_district,
                    municipality=municipality
                )
                all_loaded.update(elections)
            elif api_format == 'wabsti':
                elections = import_elections_wabsti(
                    election_type,
                    principal,
                    domain,
                    app_session,
                    number_of_mandates=number_of_mandates,
                    date_=date_,
                    domain_segment=domain_segment,
                    dataset_name=dataset_name,
                    has_expats=has_expats,
                    election=election,
                    number=election_number,
                    district=election_district,
                    municipality=municipality
                )
                all_loaded.update(elections)

        elif model == 'parties':
            all_loaded['parties'] = import_parties_internal(
                principal,
                domain,
                dataset_name,
                election,
            )

        elif model == 'vote' and api_format == 'internal':
            votes = import_votes_internal(
                vote_type,
                principal,
                domain,
                app_session,
                date_,
                dataset_name,
                has_expats,
                vote,
                municipality
            )
            all_loaded.update(votes)

        elif model == 'vote' and api_format == 'wabsti':
            # This function is used for simple and complex votes
            votes = import_votes_wabsti(
                vote_type,
                principal,
                domain,
                app_session,
                date_,
                dataset_name,
                has_expats,
                vote,
                int(vote_number),
                municipality
            )
            all_loaded.update(votes)

        elif model == 'election_compound' and api_format == 'internal':
            compounds = import_election_compounds_internal(
                principal=principal,
                domain=domain,
                session=app_session,
                number_of_mandates=number_of_mandates,
                date_=date_,
                domain_segment=domain_segment,
                domain_supersegment=domain_supersegment,
                dataset_name=dataset_name,
                has_expats=has_expats,
                election=election,
                municipality=municipality
            )
            all_loaded.update(compounds)

        else:
            raise NotImplementedError

        if len(all_loaded) == 1:
            return list(all_loaded.values())[0]

        return all_loaded

    return _import_test_datasets


@pytest.fixture(scope="function")
def majorz_election(import_test_datasets):
    def _majorz_election(session, canton='gr'):
        return import_test_datasets(
            'internal',
            'election',
            canton,
            'federation',
            election_type='majorz',
            number_of_mandates=2,
            date_=date(2015, 1, 1),
            dataset_name='majorz-election-gr',
            has_expats=False,
            app_session=session
        )
    return _majorz_election


@pytest.fixture(scope="function")
def explanations_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Erläuterungen")
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope="function")
def upper_apportionment_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Oberzuteilung")
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope="function")
def lower_apportionment_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Unterzuteilung")
    pdf.generate()
    result.seek(0)
    return result
