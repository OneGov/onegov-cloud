from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.election_day.formats import import_party_results


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
                    'name',
                    'color',
                    'mandates',
                    'votes',
                )),
                '2015,10000,P1,#123456,1,5000',
                '2011,10000,P1,#123456,0,3000',
                '2015,10000,P2,#aabbcc,0,5000',
                '2011,10000,P2,#aabbcc,1,7000',
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors
    election.party_results

    assert sorted([
        (r.year, r.name, r.color, r.votes, r.total_votes, r.number_of_mandates)
        for r in election.party_results
    ]) == [
        (2011, 'P1', '#123456', 3000, 10000, 0),
        (2011, 'P2', '#aabbcc', 7000, 10000, 1),
        (2015, 'P1', '#123456', 5000, 10000, 1),
        (2015, 'P2', '#aabbcc', 5000, 10000, 0)
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
                    'name',
                    'color',
                    'mandates',
                    'votes',
                )),
                ','.join((
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
                )),
                ','.join((
                    '2015',
                    '5000',
                    'FDP',
                    'blue',
                    '1',
                    '10',
                )),
                ','.join((
                    '2015',
                    '5000',
                    'FDP',
                    '#123456',
                    '1',
                    '10',
                )),
                ','.join((
                    '2015',
                    '5000',
                    'FDP',
                    '#123456',
                    '1',
                    '10',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert sorted(set([(e.line, e.error.interpolate()) for e in errors])) == [
        (2, 'Invalid values'),
        (3, 'Invalid values'),
        (4, 'Invalid values'),
        (6, 'FDP/2015 was found twice')
    ]
