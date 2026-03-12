from __future__ import annotations

import tarfile

from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.election_day.formats import import_party_results_internal
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import get_tar_file_path


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_import_party_results_internal_fixtures(session: Session) -> None:
    principal = Canton('gr')

    # Test data from R.Semlic
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2019, 10, 20),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    tar_file = get_tar_file_path(
        'canton', 'gr', 'internal', 'election', 'proporz')
    with tarfile.open(tar_file, 'r:gz') as f:
        csv = f.extractfile(  # type: ignore[union-attr]
            'Nationalratswahlen_2019_sesam-test_Parteien.csv').read()

    errors = import_party_results_internal(
        election, principal, BytesIO(csv), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )
    assert not errors
    total_votes = 1750

    # Test content directly from csv
    assert [
        (
            pr.party_id, pr.name_translations, pr.total_votes,
            pr.number_of_mandates, pr.votes
        )
        for pr in election.party_results] == [
        ('01', {'de_CH': 'BDP'}, total_votes, 0, 150),
        ('02', {'de_CH': 'CVP'}, total_votes, 0, 397),
        ('03', {'de_CH': 'FDP'}, total_votes, 0, 53),
        ('04', {'de_CH': 'GLP'}, total_votes, 0, 100),
        ('05', {'de_CH': 'SP'}, total_votes, 0, 650),
        ('06', {'de_CH': 'SVP'}, total_votes, 0, 100),
        ('07', {'de_CH': 'VERDA'}, total_votes, 0, 300),
    ]

    assert election.party_panachage_results
    for pana_r in election.party_panachage_results:
        assert pana_r.votes == 0


def test_import_party_results_internal_ok(session: Session) -> None:
    principal = Canton('gr')

    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    # minimal
    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                )),
                '2015,10000,1,P1,,1,5000',
                '2011,10000,1,P1,,0,3000',
                '2015,10000,2,P2,#aabbcc,0,5000',
                '2011,10000,2,P2,#aabbdd,1,7000',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert not errors
    assert sorted([
        (
            r.year, r.party_id, r.name_translations, r.votes,
            r.total_votes, r.number_of_mandates
        )
        for r in election.party_results
    ]) == [
        (2011, '1', {'de_CH': 'P1'}, 3000, 10000, 0),
        (2011, '2', {'de_CH': 'P2'}, 7000, 10000, 1),
        (2015, '1', {'de_CH': 'P1'}, 5000, 10000, 1),
        (2015, '2', {'de_CH': 'P2'}, 5000, 10000, 0)
    ]
    assert election.colors == {
        'P2': '#aabbdd',
    }

    # with panachage results
    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                    'panachage_votes_from_1',
                    'panachage_votes_from_2',
                    'panachage_votes_from_999'
                )),
                '2015,10000,1,P1,#123456,1,5000,10,11,12',
                '2011,10000,1,P1,#123456,0,3000,13,14,15',
                '2015,10000,2,P2,#aabbcc,0,5000,20,21,22',
                '2011,10000,2,P2,#aabbee,1,7000,23,24,25',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert not errors
    assert sorted([
        (
            r.year, r.party_id, r.name_translations, r.votes,
            r.total_votes, r.number_of_mandates
        )
        for r in election.party_results
    ]) == [
        (2011, '1', {'de_CH': 'P1'}, 3000, 10000, 0),
        (2011, '2', {'de_CH': 'P2'}, 7000, 10000, 1),
        (2015, '1', {'de_CH': 'P1'}, 5000, 10000, 1),
        (2015, '2', {'de_CH': 'P2'}, 5000, 10000, 0)
    ]
    assert election.colors == {
        'P1': '#123456',
        'P2': '#aabbee',
    }
    results = sorted([
        (r.target, r.source, r.votes) for r in election.party_panachage_results
    ])
    assert results == [
        ('1', '', 12),
        ('1', '2', 11),
        ('2', '', 22),
        ('2', '1', 20),
    ]

    # with alphanumeric panachage results
    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                    'panachage_votes_from_eins.zwei',
                    'panachage_votes_from_drei_vier',
                    'panachage_votes_from_999'
                )),
                '2015,10000,eins.zwei,P1,#123456,1,5000,10,11,12',
                '2015,10000,drei_vier,P2,#aabbcc,0,5000,20,21,22',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert not errors
    assert sorted([r.party_id for r in election.party_results]) == [
        'drei_vier', 'eins.zwei'
    ]
    results = sorted([
        (r.target, r.source, r.votes) for r in election.party_panachage_results
    ])
    assert results == [
        ('drei_vier', '', 22),
        ('drei_vier', 'eins.zwei', 20),
        ('eins.zwei', '', 12),
        ('eins.zwei', 'drei_vier', 11),
    ]

    # with voters count
    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                    'voters_count',
                    'voters_count_percentage',
                )),
                '2015,10000,1,P1,#123456,1,5000,4000,50',
                '2011,10000,1,P1,#123456,0,3000,3000.,37.5',
                '2015,10000,2,P2,#aabbcc,0,5000,2000.0,25.0',
                '2011,10000,2,P2,#aabbcc,1,7000,1000.01,12.5',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert not errors
    assert sorted([
        (
            r.year, r.party_id, r.name_translations, r.votes,
            r.voters_count, r.voters_count_percentage,
            r.total_votes, r.number_of_mandates
        )
        for r in election.party_results
    ]) == [
        (
            2011, '1', {'de_CH': 'P1'}, 3000, Decimal('3000.00'),
            Decimal('37.50'), 10000, 0
        ),
        (
            2011, '2', {'de_CH': 'P2'}, 7000, Decimal('1000.01'),
            Decimal('12.50'), 10000, 1
        ),
        (
            2015, '1', {'de_CH': 'P1'}, 5000, Decimal('4000.00'),
            Decimal('50.00'), 10000, 1
        ),
        (
            2015, '2', {'de_CH': 'P2'}, 5000, Decimal('2000.00'),
            Decimal('25.00'), 10000, 0
        )
    ]
    assert election.colors == {
        'P1': '#123456',
        'P2': '#aabbcc',
    }

    # with name translations
    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'color',
                    'mandates',
                    'votes',
                    'name',
                    'name_de_ch',
                    'name_fr_ch',
                    'name_it_ch',
                    'name_rm_ch',
                )),
                '2022,1,1,#111111,1,0,Die Mitte,Die Mitte,Le Centre,'
                'Alleanza del Centro,Allianza dal Center',
                '2015,1,1,#222222,0,0,CVP,CVP,PDC,PPD,PCD',
                '2022,1,2,,0,0,,SP,PS,PS,',
                '2015,1,2,,1,0,SP,,,,',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert not errors
    assert sorted([
        (r.year, r.party_id, r.name_translations)
        for r in election.party_results
    ]) == [
        (2015, '1', {'de_CH': 'CVP', 'fr_CH': 'PDC', 'it_CH': 'PPD'}),
        (2015, '2', {'de_CH': 'SP'}),
        (2022, '1', {'de_CH': 'Die Mitte', 'fr_CH': 'Le Centre',
                     'it_CH': 'Alleanza del Centro'}),
        (2022, '2', {'de_CH': 'SP', 'fr_CH': 'PS', 'it_CH': 'PS'})
    ]
    assert election.colors == {
        'P1': '#123456',
        'P2': '#aabbcc',
        'Die Mitte': '#111111',
        'Le Centre': '#111111',
        'Alleanza del Centro': '#111111',
        'CVP': '#222222',
        'PDC': '#222222',
        'PPD': '#222222',
    }


def test_import_party_results_internal_missing_headers(
    session: Session
) -> None:

    principal = Canton('gr')

    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'mandates',
                    'votes',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        (None, "Missing columns: 'color'"),
        (None, 'No party results for year 2015')
    ]


def test_import_party_results_internal_invalid_values(
    session: Session
) -> None:

    principal = Canton('gr')

    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    raw_errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                    'voters_count',
                    'panachage_votes_from_1'
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'x x x',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                )),
                ','.join((
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                )),
                ','.join((
                    '2015',
                    '5000',
                    '1',
                    'FDP',
                    'blue',
                    '1',
                    '10',
                    '10',
                    '10',
                )),
                ','.join((
                    '2015',
                    '5000',
                    '1',
                    'FDP',
                    '#123456',
                    '1',
                    '10',
                    '10',
                    '10',
                )),
                ','.join((
                    '2015',
                    '5000',
                    '1',
                    'FDP',
                    '#123456',
                    '1',
                    '10',
                    '10',
                    '10',
                )),
                ','.join((
                    '2015',
                    '5000',
                    '2',
                    'CVP',
                    '#123456',
                    '1',
                    '10',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )
    errors = sorted({(e.line, e.error.interpolate()) for e in raw_errors})  # type: ignore[attr-defined]
    assert errors == [
        (2, 'Invalid integer: year'),
        (2, 'Not an alphanumeric: id'),
        (3, 'Invalid values'),
        (4, 'Invalid color: color'),
        (6, 'canton//2015/1 was found twice'),
        (7, 'Invalid decimal number: voters_count'),
        (7, 'Invalid integer: panachage_votes_from_1')
    ]

    # IDs don't match the IDs in the panache results
    raw_errors = import_party_results_internal(
        election,
        principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'year',
                    'total_votes',
                    'id',
                    'name',
                    'color',
                    'mandates',
                    'votes',
                    'panachage_votes_from_01',
                    'panachage_votes_from_2',
                    'panachage_votes_from_999'
                )),
                '2015,10000,1,P1,#123456,1,5000,10,11,12',
                '2011,10000,1,P1,#123456,0,3000,13,14,15',
                '2015,10000,2,P2,#aabbcc,0,5000,20,21,22',
                '2011,10000,2,P2,#aabbcc,1,7000,23,24,25',
            ))
        ).encode('utf-8')), 'text/plain',
        ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
    )

    assert raw_errors[0].error.interpolate() == (  # type: ignore[attr-defined]
        'Panachage results ids and id not consistent'
    )


def test_import_party_results_internal_domains(session: Session) -> None:
    principal = Canton('bl')

    session.add(
        ProporzElection(
            title='election',
            domain='region',
            domain_segment='Allschwil',
            date=date(2022, 11, 21),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    assert isinstance(election, ProporzElection)

    session.add(
        ElectionCompound(
            title='elections',
            domain='canton',
            date=date(2022, 11, 21)
        )
    )
    session.flush()
    compound = session.query(ElectionCompound).one()
    compound.elections = [election]

    # Election
    parties: dict[str, Any]
    for domain, segment, result, parties, panachage in (
        ('', '', set(), {'region': 'Allschwil'}, 4),
        ('region', '', set(), {'region': 'Allschwil'}, 4),
        ('region', 'Allschwil', set(), {'region': 'Allschwil'}, 4),
        ('region', 'ABC', {'No party results for year 2022'}, {}, 0),
        ('district', '', {'No party results for year 2022'}, {}, 0),
        ('district', 'Allschwil', {'No party results for year 2022'}, {}, 0),
        ('district', 'ABC', {'No party results for year 2022'}, {}, 0),
    ):
        election.party_results = []
        election.party_panachage_results = []
        errors = import_party_results_internal(
            election,
            principal,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'domain',
                        'domain_segment',
                        'year',
                        'total_votes',
                        'id',
                        'name',
                        'color',
                        'mandates',
                        'votes',
                        'panachage_votes_from_1',
                        'panachage_votes_from_2',
                        'panachage_votes_from_999'
                    )),
                    f'{domain},{segment},2022,1000,1,P1,,1,5000,1,2,3',
                    f'{domain},{segment},2022,1000,2,P2,#aabbcc,0,5000,4,5,6',
                ))
            ).encode('utf-8')), 'text/plain',
            ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
        )
        assert result == {e.error.interpolate() for e in errors or []}  # type: ignore[attr-defined]
        assert parties == {
            pr.domain: pr.domain_segment for pr in election.party_results
        }
        assert len(election.party_panachage_results) == panachage

    # Compound
    for domain, segment, result, parties, panachage in (
        ('', '', set(), {'canton': None}, 4),
        ('canton', '', set(), {'canton': None}, 4),
        ('canton', 'ABC', set(), {'canton': None}, 4),
        ('region', '', {'No party results for year 2022'}, {}, 0),
        ('region', 'ABC', {'No party results for year 2022'}, {}, 0),
        ('superregion', 'Region 1', set(), {'superregion': 'Region 1'}, 0),
        ('superregion', '', {'Invalid domain_segment: None'}, {}, 0),
        ('superregion', 'ABC', {'Invalid domain_segment: ABC'}, {}, 0),
    ):
        compound.party_results = []
        compound.party_panachage_results = []
        errors = import_party_results_internal(
            compound,
            principal,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'domain',
                        'domain_segment',
                        'year',
                        'total_votes',
                        'id',
                        'name',
                        'color',
                        'mandates',
                        'votes',
                        'panachage_votes_from_1',
                        'panachage_votes_from_2',
                        'panachage_votes_from_999'
                    )),
                    f'{domain},{segment},2022,1000,1,P1,,1,5000,1,2,3',
                    f'{domain},{segment},2022,1000,2,P2,#aabbcc,0,5000,4,5,6',
                ))
            ).encode('utf-8')), 'text/plain',
            ['de_CH', 'fr_CH', 'it_CH'], 'de_CH'
        )
        assert result == {e.error.interpolate() for e in errors or []}  # type: ignore[attr-defined]
        assert parties == {
            pr.domain: pr.domain_segment for pr in compound.party_results
        }
        assert len(compound.party_panachage_results) == panachage
