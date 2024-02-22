from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.election_day.formats import import_vote_default
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality


def test_import_default_vote_success(session):
    session.add(
        Vote(title='vote', domain='canton', date=date(2017, 5, 21))
    )
    session.flush()
    vote = session.query(Vote).one()

    # Test federal results
    principal = Canton(canton='zg')

    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Ja Stimmen',
                    'Nein Stimmen',
                    'Stimmberechtigte',
                    'Leere Stimmzettel',
                    'Ungültige Stimmzettel'
                )),
                '1711,3821,7405,16516,80,1',
                '1706,811,1298,3560,18,',
                '1709,1096,2083,5245,18,1',
                '1704,599,1171,2917,17,',
                '1701,3049,5111,13828,54,3',
                '1702,2190,3347,9687,60,',
                '1703,1497,2089,5842,15,1',
                '1708,1211,2350,5989,17,',
                '1707,1302,1779,6068,17,',
                '1710,651,743,2016,8,',
                '1705,307,522,1289,10,1',
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 1
    assert round(vote.turnout, 2) == 61.34
    assert vote.eligible_voters == 72957
    assert vote.progress == (11, 11)
    assert len(vote.proposal.results) == 11
    assert vote.proposal.yeas == 16534
    assert vote.proposal.nays == 27898
    assert vote.proposal.empty == 314
    assert vote.proposal.invalid == 7
    assert round(vote.yeas_percentage, 2) == 37.21
    assert round(vote.nays_percentage, 2) == 62.79

    # Test communal results without quarters
    principal = Municipality(
        municipality='1059', canton='lu', canton_name='Kanton Luzern'
    )
    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Ja Stimmen',
                    'Nein Stimmen',
                    'Stimmberechtigte',
                    'Leere Stimmzettel',
                    'Ungültige Stimmzettel'
                )),
                '1059,2182,4913,18690,56,27'
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 1
    assert round(vote.turnout, 2) == 38.41
    assert vote.eligible_voters == 18690
    assert vote.progress == (1, 1)
    assert len(vote.proposal.results) == 1
    assert vote.proposal.yeas == 2182
    assert vote.proposal.nays == 4913
    assert vote.proposal.empty == 56
    assert vote.proposal.invalid == 27

    # Test communal results with quarters
    principal = Municipality(
        municipality='351', canton='be', canton_name='Kanton Bern'
    )
    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Ja Stimmen',
                    'Nein Stimmen',
                    'Stimmberechtigte',
                    'Leere Stimmzettel',
                    'Ungültige Stimmzettel'
                )),
                '1,4142,1121,14431,218,2',
                '2,2907,676,9788,129,7',
                '3,3978,1043,13750,201,2',
                '4,5459,1730,19329,146,9',
                '5,3742,1139,13410,211,3',
                '6,3491,1036,12276,133,4',
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert not errors
    assert vote.last_result_change
    assert vote.completed
    assert len(vote.ballots) == 1
    assert round(vote.turnout, 2) == 37.99
    assert vote.eligible_voters == 82984
    assert vote.progress == (6, 6)
    assert len(vote.proposal.results) == 6
    assert vote.proposal.yeas == 23719
    assert vote.proposal.nays == 6745
    assert vote.proposal.empty == 1038
    assert vote.proposal.invalid == 27


def test_import_default_vote_missing_headers(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='sg')

    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Nein Stimmen',
                    'Stimmberechtigte',
                    'Leere Stimmzettel',
                    'Ungültige Stimmzettel'
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )
    assert [(e.filename, e.error.interpolate()) for e in errors] == [
        ('Proposal', "Missing columns: 'ja stimmen'")
    ]


def test_import_default_vote_invalid_values(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Ja Stimmen',
                    'Nein Stimmen',
                    'Ungültige Stimmzettel',
                    'Leere Stimmzettel',
                    'Stimmberechtigte',
                )),
                ','.join((
                    'xxx',  # ID
                    'xxx',  # Ja Stimmen
                    'xxx',  # Nein Stimmen
                    'xxx',  # Ungültige Stimmzettel
                    'xxx',  # Leere Stimmzettel
                    'xxx',  # Stimmberechtigte
                )),
                ','.join((
                    '1234',  # ID
                    '1',  # Ja Stimmen
                    '1',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '0',  # Stimmberechtigte
                )),
                ','.join((
                    '1711',  # ID
                    '1',  # Ja Stimmen
                    '1',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
                ','.join((
                    '1711',  # ID
                    '1',  # Ja Stimmen
                    '1',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )

    errors = sorted(set([
        (e.line, e.error.interpolate()) for e in errors
    ]))
    print(errors)
    assert errors == [
        (2, 'Invalid integer: id'),
        (2, 'Invalid integer: ja_stimmen'),
        (2, 'Invalid integer: leere_stimmzettel'),
        (2, 'Invalid integer: nein_stimmen'),
        (2, 'Invalid integer: stimmberechtigte'),
        (2, 'Invalid integer: ungultige_stimmzettel'),
        (3, '1234 is unknown'),
        (3, 'More cast votes than eligible voters'),
        (3, 'No eligible voters'),
        (5, '1711 was found twice')
    ]


def test_import_default_vote_expats(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    for has_expats in (False, True):
        vote.has_expats = has_expats
        errors = import_vote_default(
            vote, principal, 'proposal',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'ID',
                        'Ja Stimmen',
                        'Nein Stimmen',
                        'Ungültige Stimmzettel',
                        'Leere Stimmzettel',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '9170',  # ID
                        '20',  # Ja Stimmen
                        '10',  # Nein Stimmen
                        '0',  # Ungültige Stimmzettel
                        '0',  # Leere Stimmzettel
                        '100',  # Stimmberechtigte
                    )),
                    ','.join((
                        '0',  # ID
                        '20',  # Ja Stimmen
                        '10',  # Nein Stimmen
                        '0',  # Ungültige Stimmzettel
                        '0',  # Leere Stimmzettel
                        '100',  # Stimmberechtigte
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

        errors = import_vote_default(
            vote, principal, 'proposal',
            BytesIO((
                '\n'.join((
                    ','.join((
                        'ID',
                        'Ja Stimmen',
                        'Nein Stimmen',
                        'Ungültige Stimmzettel',
                        'Leere Stimmzettel',
                        'Stimmberechtigte',
                    )),
                    ','.join((
                        '0',  # ID
                        '20',  # Ja Stimmen
                        '10',  # Nein Stimmen
                        '0',  # Ungültige Stimmzettel
                        '0',  # Leere Stimmzettel
                        '100',  # Stimmberechtigte
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


def test_import_default_vote_temporary_results(session):
    session.add(
        Vote(title='vote', domain='federation', date=date(2017, 2, 12))
    )
    session.flush()
    vote = session.query(Vote).one()
    principal = Canton(canton='zg')

    errors = import_vote_default(
        vote, principal, 'proposal',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ID',
                    'Ja Stimmen',
                    'Nein Stimmen',
                    'Ungültige Stimmzettel',
                    'Leere Stimmzettel',
                    'Stimmberechtigte',
                )),
                ','.join((
                    '1704',  # ID
                    '20',  # Ja Stimmen
                    '10',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
                ','.join((
                    '1701',  # ID
                    '20',  # Ja Stimmen
                    '10',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
                ','.join((
                    '1702',  # ID
                    'unbekannt',  # Ja Stimmen
                    '10',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    '1',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
                ','.join((
                    '1703',  # ID
                    '20',  # Ja Stimmen
                    '10',  # Nein Stimmen
                    '1',  # Ungültige Stimmzettel
                    'unknown',  # Leere Stimmzettel
                    '100',  # Stimmberechtigte
                )),
            ))
        ).encode('utf-8')),
        'text/plain'
    )

    assert not errors
    assert sorted(
        (v.entity_id for v in vote.proposal.results if v.counted is True)
    ) == [1701, 1704]
    assert sorted(
        (v.entity_id for v in vote.proposal.results if v.counted is False)
    ) == [1702, 1703, 1705, 1706, 1707, 1708, 1709, 1710, 1711]


def test_import_default_vote_regional(session):

    def create_csv(results):
        lines = []
        lines.append((
            'ID',
            'Ja Stimmen',
            'Nein Stimmen',
            'Ungültige Stimmzettel',
            'Leere Stimmzettel',
            'Stimmberechtigte',
        ))
        for entity_id in results:
            lines.append((
                str(entity_id),  # ID
                '20',  # Ja Stimmen
                '10',  # Nein Stimmen
                '1',  # Ungültige Stimmzettel
                '1',  # Leere Stimmzettel
                '100',  # Stimmberechtigte
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

    errors = import_vote_default(
        vote, principal, 'proposal',
        *create_csv((1701, 1702))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_vote_default(
        vote, principal, 'proposal',
        *create_csv((1701,))
    )
    assert not errors
    assert vote.progress == (1, 1)
