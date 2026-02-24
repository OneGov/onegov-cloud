from __future__ import annotations

import os.path
import pytest
import re
import tarfile
import textwrap
import transaction

from collections import OrderedDict
from datetime import date
from io import BytesIO
from onegov.core.crypto import hash_password
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.election_day import ElectionDayApp
from onegov.election_day.formats import import_ech
from onegov.election_day.formats import import_election_compound_internal
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.formats import import_party_results_internal
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.hidden_by_principal import (
    always_hide_candidate_by_entity_chart_percentages as hide_chart_perc)
from onegov.election_day.hidden_by_principal import (
    hide_candidates_chart_intermediate_results as hide_cand_chart)
from onegov.election_day.hidden_by_principal import (
    hide_connections_chart_intermediate_results as hide_conn_chart)
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from onegov.pdf import Pdf
from onegov.user import User
from tests.onegov.election_day.common import create_principal
from tests.onegov.election_day.common import get_tar_file_path
from tests.shared.utils import create_app


from typing import overload, Any, Literal, Protocol, TypeAlias, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.election_day.formats.imports.common import ECHImportResultType
    from onegov.election_day.formats.imports.common import FileImportError
    from onegov.election_day.types import DomainOfInfluence
    from sqlalchemy.orm import Session

    ImportFormat: TypeAlias = Literal['internal', 'ech', 'wabstic']
    ModelType: TypeAlias = Literal[
        'election',
        'vote',
        'parties',
        'election_compound'
    ]

    class ImportTestDatasets(Protocol):
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['election'],
            principal: str,
            domain: DomainOfInfluence,
            election_type: Literal['proporz'],
            number_of_mandates: int,
            date_: date,
            domain_segment: str = '',
            *,
            dataset_name: str,
            has_expats: bool = False,
            election: ProporzElection | None = None,
            municipality: str | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[ProporzElection, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['election'],
            principal: str,
            domain: DomainOfInfluence,
            election_type: Literal['majorz'],
            number_of_mandates: int,
            date_: date,
            domain_segment: str = '',
            *,
            dataset_name: str,
            has_expats: bool = False,
            election: Election | None = None,
            municipality: str | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[Election, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['election_compound'],
            principal: str,
            domain: DomainOfInfluence,
            *,
            number_of_mandates: list[int] | tuple[int, ...],
            date_: date,
            domain_segment: list[str] | tuple[str, ...],
            domain_supersegment: list[str] | tuple[str, ...],
            dataset_name: str,
            has_expats: bool = False,
            election: ElectionCompound | None = None,
            municipality: str | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[ElectionCompound, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['parties'],
            principal: str,
            domain: DomainOfInfluence,
            *,
            dataset_name: str,
            election: ProporzElection | ElectionCompound | None = None,
            app_session: Session | None = None
        ) -> dict[str, list[FileImportError] | list[str]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['vote'],
            principal: str,
            domain: DomainOfInfluence,
            *,
            date_: date,
            dataset_name: str,
            has_expats: bool = False,
            municipality: str | None = None,
            vote_type: Literal['complex'],
            vote: ComplexVote | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[ComplexVote, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['internal'],
            model: Literal['vote'],
            principal: str,
            domain: DomainOfInfluence,
            *,
            date_: date,
            dataset_name: str,
            has_expats: bool = False,
            municipality: str | None = None,
            vote_type: Literal['simple'] = 'simple',
            vote: Vote | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[Vote, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['wabstic'],
            model: Literal['election'],
            principal: str,
            domain: DomainOfInfluence,
            election_type: Literal['proporz'],
            number_of_mandates: int,
            date_: date | None = None,
            domain_segment: str = '',
            *,
            dataset_name: str,
            has_expats: bool = False,
            election: ProporzElection | None = None,
            election_number: str = '1',
            election_district: str | None = None,
            municipality: str | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[ProporzElection, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['wabstic'],
            model: Literal['election'],
            principal: str,
            domain: DomainOfInfluence,
            election_type: Literal['majorz'],
            number_of_mandates: int,
            date_: date | None = None,
            domain_segment: str = '',
            *,
            dataset_name: str,
            has_expats: bool = False,
            election: Election | None = None,
            election_number: str = '1',
            election_district: str | None = None,
            municipality: str | None = None,
            app_session: Session | None = None
        ) -> dict[str, tuple[Election, list[FileImportError]]]: ...
        @overload
        def __call__(
            self,
            api_format: Literal['ech'],
            *,
            principal: str,
            dataset_name: str,
            app_session: Session | None = None
        ) -> dict[str, ECHImportResultType]: ...


    class ImportMajorz(Protocol):
        def __call__(
            self,
            session: Session,
            canton: str = 'gr'
        ) -> dict[str, tuple[Election, list[FileImportError]]]: ...


def bool_as_string(val: bool) -> str:
    assert isinstance(val, bool)
    return 'true' if val else 'false'


@pytest.fixture(scope='session')
def election_day_password() -> str:
    # only hash the password for the test users once per test session
    return hash_password('hunter2')


class TestApp(ElectionDayApp):
    __test__ = False
    maildir: str


def create_election_day(
    request: pytest.FixtureRequest,
    canton: str = '',
    canton_name: str = '',
    municipality: str = '',
    use_maps: bool = False,
    hide_candidate_chart_percentages: bool = hide_chart_perc,
    hide_connections_chart: bool = hide_conn_chart,
    hide_candidates_chart: bool = hide_cand_chart,
) -> TestApp:
    tmp = request.getfixturevalue('temporary_directory')

    websockets = {
        'client_url': 'ws://localhost:8766',
        'manage_url': 'ws://localhost:8766',
        'manage_token': 'super-super-secret-token'
    }
    app = create_app(TestApp, request, use_maildir=True, websockets=websockets)
    app.sms_directory = os.path.join(tmp, 'sms')
    app.configuration['d3_renderer'] = 'http://localhost:1337'
    app.session_manager.set_locale('de_CH', 'de_CH')
    municipality = f'municipality: {municipality}' if municipality else ''
    chart_percentages = bool_as_string(hide_candidate_chart_percentages)

    assert app.filestorage is not None
    app.filestorage.writetext('principal.yml', textwrap.dedent(f"""
        name: Kanton Govikon
        logo: logo.jpg
        canton: {canton}
        canton_name: {canton_name}
        {municipality}
        use_maps: {bool_as_string(use_maps)}
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
    """))

    app.session().add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('election_day_password'),
        role='admin'
    ))

    transaction.commit()

    return app


@pytest.fixture(scope="function")
def election_day_app_bl(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(request, canton="bl")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_zg(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(
        request,
        canton="zg",
        hide_candidate_chart_percentages=True)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_gr(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(request, canton="gr")
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_sg(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(
        request,
        canton="sg",
        hide_candidates_chart=True,
        hide_connections_chart=True
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_sz(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(
        request,
        canton="sz",
        hide_candidates_chart=True,
        hide_connections_chart=True
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_bern(request: pytest.FixtureRequest) -> Iterator[TestApp]:
    app = create_election_day(
        request,
        canton="be",
        canton_name="Kanton Bern",
        municipality="'351'",
        use_maps=True
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope="function")
def election_day_app_kriens(
    request: pytest.FixtureRequest
) -> Iterator[TestApp]:
    app = create_election_day(
        request,
        canton="lu",
        canton_name="Kanton Luzern",
        municipality="'1059'",
        use_maps=False
    )
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def related_link_labels() -> dict[str, str]:
    return {'de_CH': 'DE', 'fr_CH': 'FR', 'it_CH': 'IT', 'rm_CH': 'RM'}


def import_elections_internal(
    election_type: Literal['proporz', 'majorz'],
    principal: str,
    domain: str,
    session: Session,
    number_of_mandates: int,
    date_: date,
    domain_segment: str,
    dataset_name: str,
    has_expats: bool,
    election: Election | ProporzElection | None,
    municipality: str | None
) -> dict[str, tuple[Election | ProporzElection, list[FileImportError]]]:
    """
    Import test datasets in internal formats. For one election, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    # FIXME: This assertion makes the municipality parameter useless
    assert isinstance(principal, str)
    if dataset_name:
        assert '.' not in dataset_name, (
            'Remove the file ending from dataset_name')

    model_mapping = {'proporz': ProporzElection, 'majorz': Election}

    function_mapping = {
        'proporz': import_election_internal_proporz,
        'majorz': import_election_internal_majorz
    }

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
                match = re.search(r'(\d){4}', name)
                assert match, 'Put the a year into the filename'
                election_date = date(int(match.group(0)), 1, 1)
            else:
                election_date = date_

            csv_file = f.extractfile(member)
            assert csv_file is not None
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
            errors = function_mapping[election_type](  # type: ignore[operator]
                election, principal_obj, BytesIO(csv_file.read()), mimetype,
            )
            assert election.title is not None
            loaded_elections[election.title] = (election, errors)
    print(tar_fp)
    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def import_election_compounds_internal(
    principal: str,
    domain: DomainOfInfluence,
    session: Session,
    number_of_mandates: list[int] | tuple[int, ...],
    date_: date,
    domain_segment: list[str] | tuple[str, ...],
    domain_supersegment: list[str] | tuple[str, ...],
    dataset_name: str,
    has_expats: bool,
    election: ElectionCompound | None,
    municipality: str | None
) -> dict[str, tuple[ElectionCompound, list[FileImportError]]]:
    """
    Import test datasets in internal formats. For one election, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    # FIXME: This assertion makes the municipality parameter useless
    assert isinstance(principal, str)
    assert isinstance(domain_segment, (tuple, list))
    assert isinstance(domain_supersegment, (tuple, list))
    assert isinstance(number_of_mandates, (tuple, list))
    assert len(domain_segment) == len(number_of_mandates)
    assert len(domain_supersegment) == len(number_of_mandates)
    if dataset_name:
        assert '.' not in dataset_name, (
            'Remove the file ending from dataset_name')

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
                match = re.search(r'(\d){4}', name)
                assert match, 'Put the a year into the filename'
                election_date = date(int(match.group(0)), 1, 1)
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

            election.elections = elections if elections else election.elections  # type: ignore[assignment]
            assert election.number_of_mandates == sum(number_of_mandates)

            principal_obj = create_principal(principal, municipality)
            csv_file = f.extractfile(member).read()  # type: ignore[union-attr]
            errors = import_election_compound_internal(
                election, principal_obj, BytesIO(csv_file), mimetype,
            )
            assert election.title is not None
            loaded_elections[election.title] = (election, errors)

    print(tar_fp)

    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def import_parties_internal(
    principal: str,
    domain: DomainOfInfluence,
    dataset_name: str,
    election: ProporzElection | ElectionCompound,
) -> list[FileImportError] | list[str]:
    """
    Import test datasets with party results in internal formats. For one
    election, there is a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    if dataset_name:
        assert '.' not in dataset_name, (
            'Remove the file ending from dataset_name')

    tar_fp = get_tar_file_path(
        domain, principal, 'internal', 'election', 'proporz'
    )
    errors: list[FileImportError] | list[str]
    with tarfile.open(tar_fp, 'r:gz') as f:
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]
        for name, member in zip(names, members):
            if name == dataset_name:
                file = f.extractfile(member).read()  # type: ignore[union-attr]
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
    election_type: Literal['majorz', 'proporz'],
    principal: str,
    domain: DomainOfInfluence,
    session: Session,
    number_of_mandates: int,
    date_: date | None,
    domain_segment: str,
    number: str,
    district: str | None,
    dataset_name: str,
    has_expats: bool,
    election: Election | ProporzElection | None,
    municipality: str | None
) -> dict[str, tuple[Election | ProporzElection, list[FileImportError]]]:
    """
    :param principal: canton as string, e.g. zg
    :param dataset_name: If set, import this dataset having that folder name
    """
    # FIXME: This assertion makes the municipality parameter useless
    assert isinstance(principal, str)
    assert isinstance(number, str)

    model_mapping = {'proporz': ProporzElection, 'majorz': Election}
    function_mapping = {
        'proporz': import_election_wabstic_proporz,
        'majorz': import_election_wabstic_majorz
    }

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
                match = re.search(r'(\d){4}', folder)
                assert match, 'Put the a year into the filename'
                election_date = date(int(match.group(0)), 1, 1)
            else:
                election_date = date_
            if not election:
                election = model_mapping[election_type](
                    title=f'{election_type}_{api}_{folder}',
                    date=election_date,
                    number_of_mandates=number_of_mandates,
                    domain=domain,
                    domain_segment=domain_segment,
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
                    f.extractfile(f'{folder}/{name}').read()) for name in files  # type: ignore[union-attr]
            }
            mimetypes = {'mimetype_' + name.split('.')[0].lower(): mimetype
                         for name in files}

            errors = function_mapping[election_type](  # type: ignore[operator]
                election,
                principal_obj,
                number=number,
                district=district,
                **files_input,
                **mimetypes
            )
            assert election.title is not None
            loaded_elections[election.title] = (election, errors)
    assert loaded_elections, 'No election was loaded'
    return loaded_elections


def get_mimetype(archive_filename: str) -> str:
    fname = archive_filename.split('/')[-1]
    ending = fname.split('.')[-1]
    if ending.lower() in ('xlsx', 'xls'):
        return (
            'application/vnd.openxmlformats-'
            'officedocument.spreadsheetml.sheet'
        )
    else:
        return 'text/plain'


def import_votes_internal(
    vote_type: Literal['simple', 'complex'],
    principal: str,
    domain: DomainOfInfluence,
    session: Session,
    date_: date,
    dataset_name: str,
    has_expats: bool,
    vote: Vote | ComplexVote | None,
    municipality: str | None
) -> dict[str, tuple[Vote | ComplexVote, list[FileImportError]]]:
    """
    Import test datasets in internal formats. For one vote, there is
    a single file to load, so subfolders are not necessary.

    :param dataset_name: use the filename without ending
    :return:
    """
    # FIXME: This assertion makes the municipality parameter useless
    assert isinstance(principal, str)
    assert '.' not in dataset_name, 'Remove file ending from dataset_name'

    api = 'internal'
    mimetype = 'text/plain'

    model_mapping = {'simple': Vote, 'complex': ComplexVote}
    loaded_votes = OrderedDict()

    tar_fp = get_tar_file_path(domain, principal, api, 'vote', vote_type)
    with tarfile.open(tar_fp, 'r:gz') as f:
        # According to docs, both methods return the same ordering (zip..)
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            if dataset_name and dataset_name != name:
                continue
            print(f'reading {name}.csv ...')

            if not date_:
                match = re.search(r'(\d){4}', name)
                assert match, 'Put the a year into the filename'
                vote_date = date(int(match.group(0)), 1, 1)
            else:
                vote_date = date_

            csv_file = f.extractfile(member).read()  # type: ignore[union-attr]
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
            assert vote.title is not None
            loaded_votes[vote.title] = (vote, errors)
    print(tar_fp)
    assert loaded_votes, 'No vote was loaded'
    return loaded_votes


def import_mulitple_ech(
    principal: str,
    session: Session,
    dataset_name: str
) -> dict[str, ECHImportResultType]:
    """
    Import test datasets in eCH formats.

    :param dataset_name: use the filename without ending
    :return:
    """
    assert isinstance(principal, str)
    assert '.' not in dataset_name, 'Remove file ending from dataset_name'

    loaded = {}
    tar_fp = get_tar_file_path('multiple', principal, 'ech')

    with tarfile.open(tar_fp, 'r:gz') as f:
        members = f.getmembers()
        names = [fn.split('.')[0] for fn in f.getnames()]

        for name, member in zip(names, members):
            if dataset_name and dataset_name != name:
                continue

            xml_file = f.extractfile(member).read()  # type: ignore[union-attr]
            principal_obj = create_principal(principal)
            loaded[name] = import_ech(
                principal_obj, BytesIO(xml_file), session, 'de_CH'
            )

    assert loaded, 'Nothing was loaded'
    return loaded


@pytest.fixture(scope="function")
def import_test_datasets(session: Session) -> ImportTestDatasets:

    models = ('election', 'vote', 'parties', 'election_compound')
    election_types = ('majorz', 'proporz')
    apis = ('internal', 'wabstic', 'ech')
    domains = (
        'federation', 'canton', 'region', 'district', 'municipality', 'none'
    )
    vote_types = ('simple', 'complex')

    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['election'],
        principal: str,
        domain: DomainOfInfluence,
        election_type: Literal['proporz'],
        number_of_mandates: int,
        date_: date,
        domain_segment: str = '',
        *,
        dataset_name: str,
        has_expats: bool = False,
        election: ProporzElection | None = None,
        municipality: str | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[ProporzElection, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['election'],
        principal: str,
        domain: DomainOfInfluence,
        election_type: Literal['majorz'],
        number_of_mandates: int,
        date_: date,
        domain_segment: str = '',
        *,
        dataset_name: str,
        has_expats: bool = False,
        election: Election | None = None,
        municipality: str | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[Election, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['election_compound'],
        principal: str,
        domain: DomainOfInfluence,
        *,
        number_of_mandates: list[int] | tuple[int, ...],
        date_: date,
        domain_segment: list[str] | tuple[str, ...],
        domain_supersegment: list[str] | tuple[str, ...],
        dataset_name: str,
        has_expats: bool = False,
        election: ElectionCompound | None = None,
        municipality: str | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[ElectionCompound, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['parties'],
        principal: str,
        domain: DomainOfInfluence,
        *,
        dataset_name: str,
        election: ProporzElection | ElectionCompound | None = None,
        app_session: Session | None = None
    ) -> dict[str, list[FileImportError] | list[str]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['vote'],
        principal: str,
        domain: DomainOfInfluence,
        *,
        date_: date,
        dataset_name: str,
        has_expats: bool = False,
        municipality: str | None = None,
        vote_type: Literal['complex'],
        vote: ComplexVote | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[ComplexVote, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['internal'],
        model: Literal['vote'],
        principal: str,
        domain: DomainOfInfluence,
        *,
        date_: date,
        dataset_name: str,
        has_expats: bool = False,
        municipality: str | None = None,
        vote_type: Literal['simple'] = 'simple',
        vote: Vote | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[Vote, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['wabstic'],
        model: Literal['election'],
        principal: str,
        domain: DomainOfInfluence,
        election_type: Literal['proporz'],
        number_of_mandates: int,
        date_: date | None = None,
        domain_segment: str = '',
        *,
        dataset_name: str,
        has_expats: bool = False,
        election: ProporzElection | None = None,
        election_number: str = '1',
        election_district: str | None = None,
        municipality: str | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[ProporzElection, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['wabstic'],
        model: Literal['election'],
        principal: str,
        domain: DomainOfInfluence,
        election_type: Literal['majorz'],
        number_of_mandates: int,
        date_: date | None = None,
        domain_segment: str = '',
        *,
        dataset_name: str,
        has_expats: bool = False,
        election: Election | None = None,
        election_number: str = '1',
        election_district: str | None = None,
        municipality: str | None = None,
        app_session: Session | None = None
    ) -> dict[str, tuple[Election, list[FileImportError]]]: ...
    @overload
    def _import_test_datasets(
        api_format: Literal['ech'],
        *,
        principal: str,
        dataset_name: str,
        app_session: Session | None = None
    ) -> dict[str, ECHImportResultType]: ...
    def _import_test_datasets(
        api_format: ImportFormat,
        model: ModelType | None = None,
        principal: str | None = None,
        domain: DomainOfInfluence | None = None,
        election_type: Literal['majorz', 'proporz'] | None = None,
        number_of_mandates: int | list[int] | tuple[int, ...] | None = None,
        date_: date | None = None,
        domain_segment: str | list[str] | tuple[str, ...] = '',
        domain_supersegment: list[str] | tuple[str, ...] = (),
        dataset_name: str | None = None,
        has_expats: bool = False,
        election: Election | ElectionCompound | None = None,
        election_number: str = '1',
        election_district: str | None = None,
        municipality: str | None = None,
        vote_type: Literal['simple', 'complex'] = 'simple',
        vote: Vote | ComplexVote | None = None,
        app_session: Session | None = None
    ) -> dict[str, Any]:

        if app_session is None:
            app_session = session

        assert api_format in apis, 'API format not defined or not available'
        assert principal, 'Define a single principal'
        assert dataset_name, 'dataset_name is required'
        if api_format != 'ech':
            assert domain in domains
            assert model in models, 'Model not defined or not available'

            if not election:
                assert domain in domains, f'Possible domains: {domains}'
                if election_type:
                    assert election_type in election_types

            if model == 'vote':
                assert vote_type in vote_types

        all_loaded: dict[str, Any] = OrderedDict()
        if model == 'election':
            assert election_type, 'Election Type is needed to load fixture'
            assert number_of_mandates is not None
            assert domain is not None
            assert election is None or isinstance(election, Election)
            assert isinstance(number_of_mandates, int)
            assert isinstance(domain_segment, str)
            if api_format == 'internal':
                assert date_ is not None
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

        elif model == 'parties':
            assert domain is not None
            if TYPE_CHECKING:
                # FIXME: For some reason we're passing a majorz election
                #        in some test cases, which seems weird
                assert isinstance(election, ProporzElection)
            all_loaded['parties'] = import_parties_internal(
                principal,
                domain,
                dataset_name,
                election,
            )

        elif model == 'vote' and api_format == 'internal':
            assert domain is not None
            assert date_ is not None
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

        elif model == 'election_compound' and api_format == 'internal':
            assert domain is not None
            assert number_of_mandates is not None
            assert date_ is not None
            assert domain_segment is not None
            assert election is None or isinstance(election, ElectionCompound)
            assert isinstance(number_of_mandates, (list, tuple))
            assert isinstance(domain_segment, (list, tuple))
            assert isinstance(domain_supersegment, (list, tuple))
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

        elif api_format == 'ech':
            assert dataset_name is not None
            items = import_mulitple_ech(
                principal=principal,
                session=session,
                dataset_name=dataset_name
            )
            all_loaded.update(items)

        else:
            raise NotImplementedError

        return all_loaded

    return _import_test_datasets


@pytest.fixture(scope="function")
def majorz_election(import_test_datasets: ImportTestDatasets) -> ImportMajorz:
    def _majorz_election(
        session: Session,
        canton: str = 'gr'
    ) -> dict[str, tuple[Election, list[FileImportError]]]:
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
def explanations_pdf() -> BytesIO:
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Erläuterungen")
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope="function")
def upper_apportionment_pdf() -> BytesIO:
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Oberzuteilung")
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope="function")
def lower_apportionment_pdf() -> BytesIO:
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Unterzuteilung")
    pdf.generate()
    result.seek(0)
    return result


@pytest.fixture(scope="session", autouse=True)
def enter_observer_scope() -> None:
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(ElectionDayApp)
