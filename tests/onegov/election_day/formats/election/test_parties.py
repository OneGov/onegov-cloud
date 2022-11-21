import tarfile

from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.election_day.formats import import_party_results
from tests.onegov.election_day.common import get_tar_file_path


def test_import_party_results_fixtures(session):
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

    tar_file = get_tar_file_path(
        'canton', 'gr', 'internal', 'election', 'proporz')
    with tarfile.open(tar_file, 'r:gz') as f:
        csv = f.extractfile(
            'Nationalratswahlen_2019_sesam-test_Parteien.csv').read()

    errors = import_party_results(
        election, BytesIO(csv), 'text/plain',
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

    assert election.panachage_results
    for pana_r in election.panachage_results:
        assert pana_r.votes == 0


def test_import_party_results(session):
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

    # minimal
    errors = import_party_results(
        election,
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
    errors = import_party_results(
        election,
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
        (r.target, r.source, r.votes) for r in election.panachage_results
    ])
    assert results == [
        ('1', '', 12),
        ('1', '2', 11),
        ('2', '', 22),
        ('2', '1', 20),
    ]

    # with voters count
    errors = import_party_results(
        election,
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
    errors = import_party_results(
        election,
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


def test_import_party_results_missing_headers(session):
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

    errors = import_party_results(
        election,
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
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        (None, "Missing columns: 'color'"),
        (None, 'No party results for year 2015')
    ]


def test_import_party_results_invalid_values(session):
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

    errors = import_party_results(
        election,
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
                    'xxx',
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
    errors = sorted(set([(e.line, e.error.interpolate()) for e in errors]))
    assert errors == [
        (2, 'Invalid integer: year'),
        (2, 'Not an alphanumeric: id'),
        (3, 'Invalid values'),
        (4, 'Invalid color: color'),
        (6, '1/2015 was found twice'),
        (7, 'Invalid decimal number: voters_count'),
        (7, 'Invalid integer: panachage_votes_from_1')
    ]

    # IDs don't match the IDs in the panache results
    errors = import_party_results(
        election,
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

    assert errors[0].error.interpolate() == (
        'Panachage results ids and id not consistent'
    )
