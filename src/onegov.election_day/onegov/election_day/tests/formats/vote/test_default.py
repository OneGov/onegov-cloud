from datetime import date
from io import BytesIO
from onegov.ballot import Vote
from onegov.election_day.formats import import_vote_default
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality


def test_import_default_vote(session):
    session.add(
        Vote(title='vote', domain='municipality', date=date(2017, 5, 21))
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
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 61.34
    assert vote.eligible_voters == 72957
    assert vote.progress == (11, 11)
    assert vote.proposal.results.count() == 11
    assert vote.proposal.yeas == 16534
    assert vote.proposal.nays == 27898
    assert vote.proposal.empty == 314
    assert vote.proposal.invalid == 7
    assert round(vote.yeas_percentage, 2) == 37.21
    assert round(vote.nays_percentage, 2) == 62.79

    # Test communal results without quarters
    principal = Municipality(municipality='1059')
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
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 38.41
    assert vote.eligible_voters == 18690
    assert vote.progress == (1, 1)
    assert vote.proposal.results.count() == 1
    assert vote.proposal.yeas == 2182
    assert vote.proposal.nays == 4913
    assert vote.proposal.empty == 56
    assert vote.proposal.invalid == 27

    # Test communal results with quarters
    principal = Municipality(municipality='351')
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
    assert vote.completed
    assert vote.ballots.count() == 1
    assert round(vote.turnout, 2) == 37.99
    assert vote.eligible_voters == 82984
    assert vote.progress == (6, 6)
    assert vote.proposal.results.count() == 6
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

    assert sorted(set([
        (e.line, e.error.interpolate()) for e in errors
    ])) == [
        (2, 'Could not read nays'),
        (2, 'Could not read the eligible voters'),
        (2, 'Could not read the empty votes'),
        (2, 'Could not read the invalid votes'),
        (2, 'Could not read yeas'),
        (2, 'Invalid id'),
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
    assert [(e.line, e.error.interpolate()) for e in errors] == [
        (3, '0 was found twice'),
    ]

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
    assert not errors
    assert vote.proposal.results.filter_by(entity_id=0).one().yeas == 20


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
                    '0',  # ID
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
        (v.entity_id for v in vote.proposal.results.filter_by(counted=True))
    ) == [0, 1701]
    assert sorted(
        (v.entity_id for v in vote.proposal.results.filter_by(counted=False))
    ) == [1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711]
