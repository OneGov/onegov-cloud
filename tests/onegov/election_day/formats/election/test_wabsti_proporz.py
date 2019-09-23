from datetime import date
from io import BytesIO
from onegov.ballot import Election, PanachageResult
from onegov.ballot import ProporzElection
from onegov.election_day.formats import import_election_wabsti_proporz
from onegov.election_day.models import Canton

from tests.onegov.election_day.common import print_errors


def test_import_wabsti_proporz_cantonal(session, import_test_datasets):

    principal = 'zg'

    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'canton',
        election_type='proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=3,
        dataset_name='nationalratswahlen-2015-minimum',
    )
    assert not errors
    assert election.completed
    assert election.progress == (11, 11)
    assert election.results.count() == 11
    assert election.progress == (11, 11)
    assert round(election.turnout, 2) == 0
    assert election.eligible_voters == 0
    assert election.accounted_ballots == 0
    assert election.accounted_votes == 0
    assert election.received_ballots == 0
    assert election.blank_ballots == 0
    assert election.invalid_ballots == 0
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        82, 117, 132, 144, 168, 218, 222, 235, 269, 345, 394, 488, 490, 545,
        550, 555, 559, 561, 607, 629, 637, 684, 929, 1043, 1142, 1159, 1163,
        1206, 1256, 1327, 1378, 1394, 1706, 1823, 1874, 2190, 2303, 2607,
        2987, 3240, 3606, 3637, 3859, 3908, 4093, 5629, 7206, 10174, 16134,
        17034
    ]
    assert election.absolute_majority is None
    assert election.allocated_mandates == 0

    # Test panachage results
    panachage_results = session.query(PanachageResult)
    panachage_results = panachage_results.filter_by(owner=election.id).all()
    assert panachage_results
    for pa_result in panachage_results:
        assert len(pa_result.target) > 10, 'target must be a casted uuid'

    # Test panachage results for ALG list
    test_list = election.lists.first()
    assert test_list.list_id == '01'
    votes_panachage_csv = 1614  # count all where source != target

    panachge_vote_count = 0
    for result in test_list.panachage_results:
        panachge_vote_count += result.votes
    assert panachge_vote_count == votes_panachage_csv


def test_import_wabsti_proporz_cantonal_complete(
        session, import_test_datasets):

    principal = 'zg'

    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'canton',
        election_type='proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=3,
        dataset_name='nationalratswahlen-2015-complete',
    )

    assert not errors
    assert election.completed
    assert election.progress == (11, 11)
    assert round(election.turnout, 2) == 53.74
    assert election.eligible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.received_ballots == 40200
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        82, 117, 132, 144, 168, 218, 222, 235, 269, 345, 394, 488, 490, 545,
        550, 555, 559, 561, 607, 629, 637, 684, 929, 1043, 1142, 1159, 1163,
        1206, 1256, 1327, 1378, 1394, 1706, 1823, 1874, 2190, 2303, 2607,
        2987, 3240, 3606, 3637, 3859, 3908, 4093, 5629, 7206, 10174, 16134,
        17034
    ]
    assert election.absolute_majority is None
    assert election.allocated_mandates == 3
    assert sorted(election.elected_candidates) == [
        ('Bruno', 'Pezzatti'), ('Gerhard', 'Pfister'), ('Thomas', 'Aeschi')
    ]
    assert sorted((l.votes for l in election.lists)) == [
        347, 575, 807, 1128, 1333, 1701, 2186, 3314, 4178, 4299, 4436, 5844,
        6521, 8868, 16285, 24335, 30532
    ]
    assert sorted((c.votes for c in election.list_connections)) == [
        0, 1128, 4178, 8352, 16048, 20584, 30856, 35543
    ]


def test_import_wabsti_proporz_regional_sg(session, import_test_datasets):
    principal = 'sg'

    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'region',
        election_type='proporz',
        date_=date(2015, 10, 18),
        number_of_mandates=17,
        dataset_name='kantonsratswahlen-2016',
    )
    assert not errors
    assert election.completed
    assert election.progress == (13, 13)
    assert round(election.turnout, 2) == 46.86
    assert election.eligible_voters == 41843
    assert election.accounted_ballots == 19270
    assert election.accounted_votes == 318662
    assert election.received_ballots == 19607
    assert election.blank_ballots == 31
    assert election.invalid_ballots == 306
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        385, 527, 555, 583, 608, 754, 857, 865, 950, 1133, 1200, 1201, 1303,
        1341, 1406, 1434, 1444, 1450, 1454, 1515, 1520, 1577, 1588, 1615,
        1689, 1691, 1734, 1830, 1863, 1864, 2077, 2082, 2151, 2159, 2249,
        2328, 2374, 2460, 2524, 2552, 2571, 2653, 2699, 2779, 2916, 2919,
        3070, 3098, 3296, 3299, 3374, 3546, 3617, 3778, 3901, 4356, 4437,
        4716, 4784, 4849, 4999, 5136, 5211, 5229, 5251, 5376, 5564, 5610,
        5950, 5965, 5965, 6078, 6085, 6184, 6435, 6738, 6901, 6949, 7152,
        7415, 9055, 9144, 9242
    ]
    assert election.absolute_majority is None
    assert election.allocated_mandates == 17
    assert sorted(election.elected_candidates) == [
        ('Alexander', 'Bartl'),
        ('Andreas', 'Broger'),
        ('Christian', 'Willi'),
        ('Laura', 'Bucher'),
        ('Marcel', 'Dietsche'),
        ('Markus', 'Wüst'),
        ('Meinrad', 'Gschwend'),
        ('Michael', 'Schöbi'),
        ('Mike', 'Egger'),
        ('Patrick', 'Dürr'),
        ('Peter', 'Eggenberger'),
        ('Peter', 'Kuster'),
        ('Remo', 'Maurer'),
        ('Rolf', 'Huber'),
        ('Sandro', 'Hess'),
        ('Stefan', 'Britschgi'),
        ('Walter', 'Freund')
    ]
    assert sorted((l.votes for l in election.lists)) == [
        12568, 15823, 36027, 61935, 75656, 116653
    ]


def test_import_wabsti_proporz_utf16(session):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            date=date(2011, 10, 23),
            number_of_mandates=1,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabsti_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste',
                    'LV',
                    'LUV',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste_KandID',
                    'ignore1',
                    'ignore2',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'StimBerTotal',
                    'WZEingegangen',
                    'WZLeer',
                    'WZUngueltig',
                    'StmWZVeraendertLeerAmtlLeer',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
    )
    assert [e.error for e in errors] == ['No data found']


def test_import_wabsti_proporz_missing_headers(session):
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
    principal = Canton(canton='sg')

    errors = import_election_wabsti_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste',
                    'LUV',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'ignore1',
                    'ignore2',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'StimBerTotal',
                    'WZEingegangen',
                    'WZUngueltig',
                    'StmWZVeraendertLeerAmtlLeer',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [
        ('Elected Candidates', "Missing columns: 'liste_kandid'"),
        ('Election statistics', "Missing columns: 'wzleer'"),
        ('List connections', "Missing columns: 'lv'"),
        ('Results', "Missing columns: 'liste_kandid'")
    ]


def test_import_wabsti_proporz_invalid_values(session):
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
    principal = Canton(canton='sg')

    errors = import_election_wabsti_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
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
                    '1234',
                    '7',
                    'xxx',
                    'xxx',
                    '8',
                    '9',
                    '50',
                    '60',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste',
                    'LV',
                    'LUV',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Liste_KandID',
                    'ignore1',
                    'ignore2',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                )),
                ','.join((
                    '1',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Einheit_Name',
                    'StimBerTotal',
                    'WZEingegangen',
                    'WZLeer',
                    'WZUngueltig',
                    'StmWZVeraendertLeerAmtlLeer',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    print_errors(errors)
    errors = sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ])
    assert errors == [
        ('Elected Candidates', 2, 'Invalid integer: liste_kandid'),
        ('Elected Candidates', 3, 'Unknown candidate'),
        ('Election statistics', 2, 'Invalid integer: einheit_bfs'),
        ('List connections', 2, 'Not an alphanumeric: liste'),
        ('Results', 2, 'Invalid integer: einheit_bfs'),
        ('Results', 2, 'Invalid integer: kand_stimmentotal'),
        ('Results', 2, 'Invalid integer: liste_kandid'),
        ('Results', 2, 'Invalid integer: liste_parteistimmentotal'),
        ('Results', 2, 'Not an alphanumeric: liste_id'),
        ('Results', 2, 'Not an alphanumeric: liste_id'),
        ('Results', 3, '1234 is unknown')
    ]


def test_import_wabsti_proporz_expats(session):
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
    principal = Canton(canton='sg')

    for expats in (False, True):
        election.expats = expats
        for entity_id in (9170, 0):
            errors = import_election_wabsti_proporz(
                election, principal,
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'Einheit_BFS',
                            'Liste_KandID',
                            'Kand_Nachname',
                            'Kand_Vorname',
                            'Liste_ID',
                            'Liste_Code',
                            'Kand_StimmenTotal',
                            'Liste_ParteistimmenTotal',
                        )),
                        ','.join((
                            str(entity_id),
                            '7',
                            'xxx',
                            'xxx',
                            '8',
                            '9',
                            '50',
                            '60',
                        )),
                    ))
                ).encode('utf-8')), 'text/plain',
            )
            errors = [(e.line, e.error.interpolate()) for e in errors]
            candidate = election.candidates.first()
            if expats:
                assert errors == []
                assert candidate.results.one().election_result.entity_id == 0
                assert candidate.votes == 50
            else:
                assert errors == [(None, 'No data found')]
                assert candidate is None


def test_import_wabsti_proporz_temporary_results(session):
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
    principal = Canton(canton='sg')

    errors = import_election_wabsti_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
                ','.join((
                    '3203',
                    '7',
                    'xxx',
                    'xxx',
                    '8',
                    '9',
                    '50',
                    '60',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )

    assert not errors

    # 1 Present, 76 Missing
    assert election.progress == (1, 77)


def test_import_wabsti_proporz_regional(session):
    session.add(
        ProporzElection(
            title='election',
            domain='region',
            date=date(2018, 2, 19),
            number_of_mandates=1
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal_zg = Canton(canton='zg')
    principal_sg = Canton(canton='sg')

    # Too many districts
    for distinct in (False, True):
        election.distinct = distinct
        expected = ['No clear district'] if distinct else []

        errors = import_election_wabsti_proporz(
            election, principal_zg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Einheit_BFS',
                        'Liste_KandID',
                        'Kand_Nachname',
                        'Kand_Vorname',
                        'Liste_ID',
                        'Liste_Code',
                        'Kand_StimmenTotal',
                        'Liste_ParteistimmenTotal',
                    )),
                    ','.join((
                        '1701',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                    ','.join((
                        '1702',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert [error.error for error in errors] == expected

        errors = import_election_wabsti_proporz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Einheit_BFS',
                        'Liste_KandID',
                        'Kand_Nachname',
                        'Kand_Vorname',
                        'Liste_ID',
                        'Liste_Code',
                        'Kand_StimmenTotal',
                        'Liste_ParteistimmenTotal',
                    )),
                    ','.join((
                        '3231',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                    ','.join((
                        '3276',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert [error.error for error in errors] == expected

    # OK
    election.distinct = True
    errors = import_election_wabsti_proporz(
        election, principal_zg,
        BytesIO((
            '\n'.join((
                ','.join((
                    'Einheit_BFS',
                    'Liste_KandID',
                    'Kand_Nachname',
                    'Kand_Vorname',
                    'Liste_ID',
                    'Liste_Code',
                    'Kand_StimmenTotal',
                    'Liste_ParteistimmenTotal',
                )),
                ','.join((
                    '1701',
                    '7',
                    'xxx',
                    'xxx',
                    '8',
                    '9',
                    '50',
                    '60',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert not errors
    assert election.progress == (1, 1)

    # Temporary
    for distinct, total in ((False, 1), (True, 13)):
        election.distinct = distinct

        errors = import_election_wabsti_proporz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'Einheit_BFS',
                        'Liste_KandID',
                        'Kand_Nachname',
                        'Kand_Vorname',
                        'Liste_ID',
                        'Liste_Code',
                        'Kand_StimmenTotal',
                        'Liste_ParteistimmenTotal',
                    )),
                    ','.join((
                        '3231',
                        '7',
                        'xxx',
                        'xxx',
                        '8',
                        '9',
                        '50',
                        '60',
                    )),
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert not errors
        assert election.progress == (1, total)
