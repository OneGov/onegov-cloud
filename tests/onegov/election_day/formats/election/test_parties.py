import tarfile
from datetime import date
from io import BytesIO

import pytest
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.election_day.formats import import_party_results
from tests.onegov.election_day.common import get_tar_file_path, print_errors


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

    errors = import_party_results(election, BytesIO(csv), 'text/plain')
    print_errors(errors)
    assert not errors
    total_votes = 1750

    # Test content directly from csv
    assert [
        (pr.name, pr.total_votes, pr.number_of_mandates, pr.votes)
        for pr in election.party_results] == [
        ('BDP', total_votes, 0, 150),
        ('CVP', total_votes, 0, 397),
        ('FDP', total_votes, 0, 53),
        ('GLP', total_votes, 0, 100),
        ('SP', total_votes, 0, 650),
        ('SVP', total_votes, 0, 100),
        ('VERDA', total_votes, 0, 300),
    ]

    assert election.panachage_results
    for pana_r in election.panachage_results:
        # assert len(pana_r.target) > 10, 'target must be casted list.id'
        if not pana_r.votes == 0:
            print(pana_r.source, pana_r.target)
        assert pana_r.votes == 0, "Panachage votes from own list don't count"


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
                '2015,10000,1,P1,#123456,1,5000',
                '2011,10000,1,P1,#123456,0,3000',
                '2015,10000,2,P2,#aabbcc,0,5000',
                '2011,10000,2,P2,#aabbcc,1,7000',
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors
    assert sorted([
        (r.year, r.name, r.color, r.votes, r.total_votes, r.number_of_mandates)
        for r in election.party_results
    ]) == [
        (2011, 'P1', '#123456', 3000, 10000, 0),
        (2011, 'P2', '#aabbcc', 7000, 10000, 1),
        (2015, 'P1', '#123456', 5000, 10000, 1),
        (2015, 'P2', '#aabbcc', 5000, 10000, 0)
    ]


@pytest.mark.parametrize('wrong_id,error', [
    ('01', "Panachage results ids and id not consistent"),
])
def test_import_party_results_panachage_invalid_values(
        session, wrong_id, error):

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
                        f'panachage_votes_from_{wrong_id}',
                        'panachage_votes_from_2',
                        'panachage_votes_from_999'
                    )),
                    '2015,10000,1,P1,#123456,1,5000,10,11,12',
                    '2011,10000,1,P1,#123456,0,3000,13,14,15',
                    '2015,10000,2,P2,#aabbcc,0,5000,20,21,22',
                    '2011,10000,2,P2,#aabbcc,1,7000,23,24,25',
                ))
                ).encode('utf-8')), 'text/plain'
    )

    assert errors[0].error.interpolate() == error


def test_import_party_results_with_panachage(session):
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
                    'panachage_votes_from_1',
                    'panachage_votes_from_2',
                    'panachage_votes_from_999'
                )),
                '2015,10000,1,P1,#123456,1,5000,10,11,12',
                '2011,10000,1,P1,#123456,0,3000,13,14,15',
                '2015,10000,2,P2,#aabbcc,0,5000,20,21,22',
                '2011,10000,2,P2,#aabbcc,1,7000,23,24,25',
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors
    assert sorted([
        (r.year, r.name, r.color, r.votes, r.total_votes, r.number_of_mandates)
        for r in election.party_results
    ]) == [
        (2011, 'P1', '#123456', 3000, 10000, 0),
        (2011, 'P2', '#aabbcc', 7000, 10000, 1),
        (2015, 'P1', '#123456', 5000, 10000, 1),
        (2015, 'P2', '#aabbcc', 5000, 10000, 0)
    ]

    results = sorted([
        (r.target, r.source, r.votes) for r in election.panachage_results
    ])
    print(results)
    assert results == [
        ('P1', '', 12),
        ('P1', 'P2', 11),
        ('P2', '', 22),
        ('P2', 'P1', 20),
    ]


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
        ).encode('utf-8')), 'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        (None, "Missing columns: 'color'")
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
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    errors = sorted(set([(e.line, e.error.interpolate()) for e in errors]))
    print(errors)
    assert errors == [
        (2, 'Invalid integer: year'),
        (2, 'Not an alphanumeric: id'),
        (3, 'Invalid values'),
        (4, 'Invalid values'),
        (6, 'FDP/2015 was found twice'),
        (7, 'Invalid integer: panachage_votes_from_1')
    ]
