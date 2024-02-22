import tarfile
from datetime import date
from io import BytesIO
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.formats import import_vote_wabsti
from onegov.election_day.models import Canton
from tests.onegov.election_day.common import get_tar_file_path, \
    create_principal


def test_import_wabsti_vote(session):
    principal = 'sg'
    domain = 'federation'

    session.add(
        Vote(title='vote', domain=domain, date=date(2016, 2, 28))
    )
    session.flush()
    vote = session.query(Vote).one()
    tar_file = get_tar_file_path(domain, principal, 'wabsti', 'vote')
    # The tar file contains vote results from SG with 4 simple federal votes
    # from the 28.02.2016 and one complex cantonal vote from the 27.11.2011
    with tarfile.open(tar_file, 'r|gz') as f:
        csv = f.extractfile(f.next()).read()

    # Test federal results
    principal = create_principal(principal)
    vote.has_expats = True
    for number, yeas, nays, yeas_p, nays_p, turnout in (
        (1, 102759, 91138, 53.0, 47.0, 61.7),
        (2, 90715, 106942, 45.9, 54.1, 62.4),
        (3, 71087, 119423, 37.3, 62.7, 61.1),
        (4, 109503, 85790, 56.1, 43.9, 62.0),
    ):
        errors = import_vote_wabsti(
            vote, principal, number, BytesIO(csv), 'text/plain'
        )
        assert not errors
        assert vote.last_result_change
        assert vote.completed
        assert len(vote.proposal.results) == 78
        assert vote.yeas == yeas
        assert vote.nays == nays
        assert round(vote.yeas_percentage, 1) == yeas_p
        assert round(vote.nays_percentage, 1) == nays_p
        assert round(vote.turnout, 1) == turnout
    #
    # Test cantonal vote
    session.add(
        ComplexVote(title='vote', domain='canton', date=date(2011, 11, 27))
    )
    session.flush()
    vote = session.query(ComplexVote).one()

    errors = import_vote_wabsti(
        vote, principal, 5, BytesIO(csv), 'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 3
    assert round(vote.turnout, 1) == 43.3

    assert len(vote.proposal.results) == 85
    assert vote.proposal.yeas == 62049
    assert vote.proposal.nays == 57450
    assert round(vote.proposal.yeas_percentage, 1) == 51.9
    assert round(vote.proposal.nays_percentage, 1) == 48.1
    assert round(vote.proposal.turnout, 1) == 43.3

    assert len(vote.counter_proposal.results) == 85
    assert vote.counter_proposal.yeas == 71277
    assert vote.counter_proposal.nays == 41107
    assert round(vote.counter_proposal.yeas_percentage, 1) == 63.4
    assert round(vote.counter_proposal.nays_percentage, 1) == 36.6
    assert round(vote.counter_proposal.turnout, 1) == 43.3

    assert len(vote.tie_breaker.results) == 85
    assert vote.tie_breaker.yeas == 54987
    assert vote.tie_breaker.nays == 64681
    assert round(vote.tie_breaker.yeas_percentage, 1) == 45.9
    assert round(vote.tie_breaker.nays_percentage, 1) == 54.1
    assert round(vote.tie_breaker.turnout, 1) == 43.3


def test_import_wabsti_vote_utf16(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_wabsti(
        vote, principal, 0,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Vorlage-Nr.',
                    'BfS-Nr.',
                    'Stimmberechtigte',
                    'leere SZ',
                    'ungültige SZ',
                    'Ja',
                    'Nein',
                    'InitOAntw',
                    'GegenvJa',
                    'GegenvNein',
                    'GegenvOAntw',
                    'StichfrJa',
                    'StichfrNein',
                    'StichfrOAntw',
                    'StimmBet',
                )),
            ))
        ).encode('utf-16-le')),
        'text/plain'
    )
    assert [e.error for e in errors] == ['No data found']


def test_import_wabsti_vote_missing_headers(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_wabsti(
        vote, principal, 0,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Vorlage-Nr.',
                    'Stimmberechtigte',
                    'leere SZ',
                    'ungültige SZ',
                    'Ja',
                    'Nein',
                    'InitOAntw',
                    'GegenvJa',
                    'GegenvOAntw',
                    'StichfrJa',
                    'StichfrNein',
                    'StichfrOAntw',
                    'StimmBet',
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        (None, "Missing columns: 'bfs-nr., gegenvnein'")
    ]


def test_import_wabsti_vote_invalid_values(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_wabsti(
        vote, principal, 0,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Vorlage-Nr.',
                    'BfS-Nr.',
                    'Stimmberechtigte',
                    'leere SZ',
                    'ungültige SZ',
                    'Ja',
                    'Nein',
                    'InitOAntw',
                    'GegenvJa',
                    'GegenvNein',
                    'GegenvOAntw',
                    'StichfrJa',
                    'StichfrNein',
                    'StichfrOAntw',
                    'StimmBet',
                )),
                ','.join((
                    'xxx',  # Vorlage-Nr.',
                    'xxx',  # BfS-Nr.',
                    'xxx',  # Stimmberechtigte',
                    'xxx',  # leere SZ',
                    'xxx',  # ungültige SZ',
                    'xxx',  # Ja',
                    'xxx',  # Nein',
                    'xxx',  # InitOAntw',
                    'xxx',  # GegenvJa',
                    'xxx',  # GegenvNein',
                    'xxx',  # GegenvOAntw',
                    'xxx',  # StichfrJa',
                    'xxx',  # StichfrNein',
                    'xxx',  # StichfrOAntw',
                    'xxx',  # StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '1701',  # BfS-Nr.',
                    '100',  # Stimmberechtigte',
                    '0',  # leere SZ',
                    '0',  # ungültige SZ',
                    '10',  # Ja',
                    '20',  # Nein',
                    '',  # InitOAntw',
                    '',  # GegenvJa',
                    '',  # GegenvNein',
                    '',  # GegenvOAntw',
                    '',  # StichfrJa',
                    '',  # StichfrNein',
                    '',  # StichfrOAntw',
                    '40.50',  # StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '1701',  # BfS-Nr.',
                    '100',  # Stimmberechtigte',
                    '0',  # leere SZ',
                    '0',  # ungültige SZ',
                    '10',  # Ja',
                    '20',  # Nein',
                    '',  # InitOAntw',
                    '',  # GegenvJa',
                    '',  # GegenvNein',
                    '',  # GegenvOAntw',
                    '',  # StichfrJa',
                    '',  # StichfrNein',
                    '',  # StichfrOAntw',
                    '40.50',  # StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '4448',  # BfS-Nr.',
                    '',  # Stimmberechtigte',
                    '',  # leere SZ',
                    '',  # ungültige SZ',
                    '',  # Ja',
                    '',  # Nein',
                    '',  # InitOAntw',
                    '',  # GegenvJa',
                    '',  # GegenvNein',
                    '',  # GegenvOAntw',
                    '',  # StichfrJa',
                    '',  # StichfrNein',
                    '',  # StichfrOAntw',
                    '40.50',  # StimmBet',
                )),
            ))
        ).encode('utf-8')),
        'text/plain',
    )
    errors = sorted(set([
        (e.line, e.error.interpolate()) for e in errors
    ]))
    print(errors)
    assert errors == [
        (2, 'Could not read the empty votes'),
        (2, 'Invalid float number: stimmbet'),
        (2, 'Invalid integer: bfs_nr_'),
        (2, 'Invalid integer: ja'),
        (2, 'Invalid integer: nein'),
        (2, 'Invalid integer: stimmberechtigte'),
        (2, 'Invalid integer: ungultige_sz'),
        (2, 'Invalid integer: vorlage_nr_'),
        (4, '1701 was found twice'),
        (5, '4448 is unknown')
    ]


def test_import_wabsti_vote_expats(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    for has_expats in (False, True):
        vote.has_expats = has_expats
        errors = import_vote_wabsti(
            vote, principal, 0,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Vorlage-Nr.',
                        'BfS-Nr.',
                        'Stimmberechtigte',
                        'leere SZ',
                        'ungültige SZ',
                        'Ja',
                        'Nein',
                        'InitOAntw',
                        'GegenvJa',
                        'GegenvNein',
                        'GegenvOAntw',
                        'StichfrJa',
                        'StichfrNein',
                        'StichfrOAntw',
                        'StimmBet',
                    )),
                    ','.join((
                        '0',  # Vorlage-Nr.',
                        '9170',  # BfS-Nr.',
                        '100',  # Stimmberechtigte',
                        '1',  # leere SZ',
                        '1',  # ungültige SZ',
                        '20',  # Ja',
                        '10',  # Nein',
                        '0',  # InitOAntw',
                        '0',  # GegenvJa',
                        '0',  # GegenvNein',
                        '0',  # GegenvOAntw',
                        '0',  # StichfrJa',
                        '0',  # StichfrNein',
                        '0',  # StichfrOAntw',
                        '10.0',  # StimmBet',
                    )),
                    ','.join((
                        '0',  # Vorlage-Nr.',
                        '0',  # BfS-Nr.',
                        '100',  # Stimmberechtigte',
                        '1',  # leere SZ',
                        '1',  # ungültige SZ',
                        '20',  # Ja',
                        '10',  # Nein',
                        '0',  # InitOAntw',
                        '0',  # GegenvJa',
                        '0',  # GegenvNein',
                        '0',  # GegenvOAntw',
                        '0',  # StichfrJa',
                        '0',  # StichfrNein',
                        '0',  # StichfrOAntw',
                        '10.0',  # StimmBet',
                    )),
                ))
            ).encode('utf-8')),
            'text/plain'
        )
        errors = [(e.line, e.error.interpolate()) for e in errors]
        if has_expats:
            assert errors == [(3, '0 was found twice')]
        else:
            assert errors == [(None, 'No data found')]

        errors = import_vote_wabsti(
            vote, principal, 0,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Vorlage-Nr.',
                        'BfS-Nr.',
                        'Stimmberechtigte',
                        'leere SZ',
                        'ungültige SZ',
                        'Ja',
                        'Nein',
                        'InitOAntw',
                        'GegenvJa',
                        'GegenvNein',
                        'GegenvOAntw',
                        'StichfrJa',
                        'StichfrNein',
                        'StichfrOAntw',
                        'StimmBet',
                    )),
                    ','.join((
                        '0',  # Vorlage-Nr.',
                        '9170',  # BfS-Nr.',
                        '100',  # Stimmberechtigte',
                        '1',  # leere SZ',
                        '1',  # ungültige SZ',
                        '20',  # Ja',
                        '10',  # Nein',
                        '0',  # InitOAntw',
                        '0',  # GegenvJa',
                        '0',  # GegenvNein',
                        '0',  # GegenvOAntw',
                        '0',  # StichfrJa',
                        '0',  # StichfrNein',
                        '0',  # StichfrOAntw',
                        '10.0',  # StimmBet',
                    )),
                ))
            ).encode('utf-8')),
            'text/plain'
        )
        errors = [(e.line, e.error.interpolate()) for e in errors]
        result = next(
            (r for r in vote.proposal.results if r.entity_id == 0), None
        )
        if has_expats:
            assert errors == []
            assert result.yeas == 20
        else:
            assert errors == [(None, 'No data found')]
            assert result is None


def test_import_wabsti_vote_temporary_results(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_wabsti(
        vote, principal, 0,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Vorlage-Nr.',
                    'BfS-Nr.',
                    'Stimmberechtigte',
                    'leere SZ',
                    'ungültige SZ',
                    'Ja',
                    'Nein',
                    'InitOAntw',
                    'GegenvJa',
                    'GegenvNein',
                    'GegenvOAntw',
                    'StichfrJa',
                    'StichfrNein',
                    'StichfrOAntw',
                    'StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '1703',  # BfS-Nr.',
                    '100',  # Stimmberechtigte',
                    '1',  # leere SZ',
                    '1',  # ungültige SZ',
                    '20',  # Ja',
                    '10',  # Nein',
                    '0',  # InitOAntw',
                    '0',  # GegenvJa',
                    '0',  # GegenvNein',
                    '0',  # GegenvOAntw',
                    '0',  # StichfrJa',
                    '0',  # StichfrNein',
                    '0',  # StichfrOAntw',
                    '10.0',  # StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '1701',  # BfS-Nr.',
                    '100',  # Stimmberechtigte',
                    '1',  # leere SZ',
                    '1',  # ungültige SZ',
                    '20',  # Ja',
                    '10',  # Nein',
                    '0',  # InitOAntw',
                    '0',  # GegenvJa',
                    '0',  # GegenvNein',
                    '0',  # GegenvOAntw',
                    '0',  # StichfrJa',
                    '0',  # StichfrNein',
                    '0',  # StichfrOAntw',
                    '10.0',  # StimmBet',
                )),
                ','.join((
                    '0',  # Vorlage-Nr.',
                    '1702',  # BfS-Nr.',
                    '100',  # Stimmberechtigte',
                    '1',  # leere SZ',
                    '1',  # ungültige SZ',
                    '20',  # Ja',
                    '10',  # Nein',
                    '0',  # InitOAntw',
                    '0',  # GegenvJa',
                    '0',  # GegenvNein',
                    '0',  # GegenvOAntw',
                    '0',  # StichfrJa',
                    '0',  # StichfrNein',
                    '0',  # StichfrOAntw',
                    '0',  # StimmBet',
                )),
            ))
        ).encode('utf-8')),
        'text/plain',
    )
    assert not errors
    assert sorted(
        (v.entity_id for v in vote.proposal.results if v.counted is True)
    ) == [1701, 1703]
    assert sorted(
        (v.entity_id for v in vote.proposal.results if v.counted is False)
    ) == [1702, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711]


def test_import_wabsti_vote_regional(session):

    def create_csv(results):
        lines = []
        lines.append((
            'Vorlage-Nr.',
            'BfS-Nr.',
            'Stimmberechtigte',
            'leere SZ',
            'ungültige SZ',
            'Ja',
            'Nein',
            'InitOAntw',
            'GegenvJa',
            'GegenvNein',
            'GegenvOAntw',
            'StichfrJa',
            'StichfrNein',
            'StichfrOAntw',
            'StimmBet',
        ))
        for entity_id in results:
            lines.append((
                '0',  # Vorlage-Nr.',
                str(entity_id),  # BfS-Nr.',
                '100',  # Stimmberechtigte',
                '1',  # leere SZ',
                '1',  # ungültige SZ',
                '20',  # Ja',
                '10',  # Nein',
                '0',  # InitOAntw',
                '0',  # GegenvJa',
                '0',  # GegenvNein',
                '0',  # GegenvOAntw',
                '0',  # StichfrJa',
                '0',  # StichfrNein',
                '0',  # StichfrOAntw',
                '10.0',  # StimmBet',
            ))

        return BytesIO(
            '\n'.join(
                (','.join(column for column in line)) for line in lines
            ).encode('utf-8')
        ), 'text/plain'

    session.add(
        Vote(title='vote', domain='municipality', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    vote.domain = 'municipality'
    vote.domain_segment = 'Baar'
    errors = import_vote_wabsti(
        vote, principal, 0,
        *create_csv((1701, 1702))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_vote_wabsti(
        vote, principal, 0,
        *create_csv((1701,))
    )
    assert not errors
    assert vote.progress == (1, 1)
