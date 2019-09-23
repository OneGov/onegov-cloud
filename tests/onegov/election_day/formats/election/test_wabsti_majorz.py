from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.election_day.formats import import_election_wabsti_majorz
from onegov.election_day.models import Canton


def test_import_wabsti_majorz_cantonal_simple(session, import_test_datasets):

    principal = 'sg'
    # The tar file contains
    # - cantonal results from SG from the 23.10.2011
    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'canton',
        election_type='majorz',
        number_of_mandates=1,
        date_=date(2011, 10, 23),
        dataset_name='staenderatswahlen-2011-simple',
    )

    assert not errors
    assert election.completed
    assert election.progress == (85, 85)
    assert round(election.turnout, 2) == 47.79
    assert election.eligible_voters == 304850
    assert election.accounted_ballots == 144529
    assert election.accounted_votes == 144529
    assert election.received_ballots == 145694
    assert election.blank_ballots == 942
    assert election.invalid_ballots == 223
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        36282, 53308, 54616
    ]
    assert election.absolute_majority is None
    assert election.allocated_mandates == 0


def test_import_wabsti_majorz_cantonal_complete(
        session, import_test_datasets):

    # Test cantonal election with elected candidates
    principal = 'sg'

    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'canton',
        election_type='majorz',
        number_of_mandates=1,
        date_=date(2011, 10, 23),
        dataset_name='staenderatswahlen-2011-complete',
    )
    assert not errors
    assert election.completed
    assert election.progress == (85, 85)
    assert round(election.turnout, 2) == 47.79
    assert election.eligible_voters == 304850
    assert election.accounted_ballots == 144529
    assert election.accounted_votes == 144529
    assert election.received_ballots == 145694
    assert election.blank_ballots == 942
    assert election.invalid_ballots == 223
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        36282, 53308, 54616
    ]
    assert election.absolute_majority is None
    assert election.allocated_mandates == 1
    assert election.elected_candidates == [('Paul', 'Rechsteiner')]


def test_import_wabsti_majorz_regional_sg(session, import_test_datasets):
    # - regional results from Rohrschach the 25.09.2016
    principal = 'sg'
    # Test regional election
    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'region',
        election_type='majorz',
        number_of_mandates=1,
        date_=date(2016, 9, 25),
        dataset_name='RO-Kreisgericht-Rohrschach',
    )

    assert not errors
    assert election.completed
    assert election.progress == (9, 9)
    assert round(election.turnout, 2) == 42.0
    assert election.eligible_voters == 25438
    assert election.received_ballots == 10685
    assert election.accounted_ballots == 10150
    assert election.blank_ballots == 456
    assert election.invalid_ballots == 79

    assert sorted([candidate.votes for candidate in election.candidates]) == [
        2804, 3602, 3721
    ]
    assert election.absolute_majority == 5076
    assert election.allocated_mandates == 0


def test_import_wabsti_majorz_municipal(session, import_test_datasets):
    # - communal results from the 25.09.2016
    principal = 'Au'
    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'municipality',
        election_type='majorz',
        number_of_mandates=6,
        date_=date(2016, 9, 25),
        dataset_name='Au-gemeinderat-2016',
        municipality='3231'
    )
    assert not errors
    assert election.completed
    assert election.progress == (1, 1)
    assert round(election.turnout, 2) == 27.03
    assert election.eligible_voters == 4021
    assert election.received_ballots == 1087
    assert election.accounted_ballots == 1036
    assert election.blank_ballots == 28
    assert election.invalid_ballots == 23
    assert sorted([candidate.votes for candidate in election.candidates]) == [
        556, 665, 678, 715, 790, 810, 830
    ]
    assert election.absolute_majority == 519
    assert election.allocated_mandates == 6
    assert sorted(election.elected_candidates) == [
        ('Alex', 'Frei'),
        ('Carola', 'Espanhol'),
        ('Ernst', 'Brändle'),
        ('Franco', 'Frisenda'),
        ('Gloria', 'Schöbi'),
        ('Markus', 'Bernet')
    ]


def test_import_wabsti_majorz_utf16(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2011, 10, 23),
            number_of_mandates=1,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabsti_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'StimmBer',
                    'StimmAbgegeben',
                    'StimmLeer',
                    'StimmUngueltig',
                    'KandName_1',
                    'Stimmen_1',
                    'KandName_2',
                    'Stimmen_2',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'KandID',
                    'Name',
                    'Vorname',
                )),
            ))
        ).encode('utf-16-le')), 'text/plain',
    )
    assert [e.error for e in errors] == ['No data found']


def test_import_wabsti_majorz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabsti_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'StimmBer',
                    'StimmLeer',
                    'StimmUngueltig',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'Name',
                    'Vorname',
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert sorted([(e.filename, e.error.interpolate()) for e in errors]) == [
        ('Elected Candidates', "Missing columns: 'kandid'"),
        ('Results', "Missing columns: 'bfs'"),
    ]


def test_import_wabsti_majorz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabsti_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'StimmBer',
                    'StimmAbgegeben',
                    'StimmLeer',
                    'StimmUngueltig',
                    'KandName_1',
                    'Stimmen_1',
                    'KandName_2',
                    'Stimmen_2',
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
                    'xxx',
                )),
                ','.join((
                    '',
                    '1234',
                    '100',
                    '90',
                    '1',
                    '1',
                    'Leere Zeilen',
                    '0',
                    'Ungültige Stimmen',
                    '0'
                )),
            ))
        ).encode('utf-8')), 'text/plain',
        BytesIO((
            '\n'.join((
                ','.join((
                    'KandID',
                    'Name',
                    'Vorname',
                )),
                ','.join((
                    'xxx',
                    'xxx',
                    'xxx',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )

    errors = sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ])
    print(errors)
    assert errors == [
        ('Elected Candidates', 2, 'Unknown candidate'),
        ('Results', 2, 'Invalid integer: anzmandate'),
        ('Results', 2, 'Invalid integer: bfs'),
        ('Results', 3, '1234 is unknown')
    ]


def test_import_wabsti_majorz_expats(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    for expats in (False, True):
        election.expats = expats
        for entity_id in (9170, 0):
            errors = import_election_wabsti_majorz(
                election, principal,
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'AnzMandate',
                            'BFS',
                            'StimmBer',
                            'StimmAbgegeben',
                            'StimmLeer',
                            'StimmUngueltig',
                            'KandName_1',
                            'Stimmen_1',
                            'KandName_2',
                            'Stimmen_2',
                        )),
                        ','.join((
                            '',
                            str(entity_id),
                            '100',
                            '90',
                            '1',
                            '1',
                            'Leere Zeilen',
                            '0',
                            'Ungültige Stimmen',
                            '1'
                        )),
                    ))
                ).encode('utf-8')), 'text/plain'
            )
            errors = [(e.line, e.error.interpolate()) for e in errors]
            result = election.results.filter_by(entity_id=0).first()
            if expats:
                assert errors == []
                assert result.invalid_votes == 1
            else:
                assert errors == [(None, 'No data found')]
                assert result is None


def test_import_wabsti_majorz_temporary_results(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2016, 2, 28),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_wabsti_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'StimmBer',
                    'StimmAbgegeben',
                    'StimmLeer',
                    'StimmUngueltig',
                    'KandName_1',
                    'Stimmen_1',
                    'KandName_2',
                    'Stimmen_2',
                )),
                ','.join((
                    '',
                    '3203',
                    '100',
                    '90',
                    '1',
                    '1',
                    'Leere Zeilen',
                    '0',
                    'Ungültige Stimmen',
                    '1'
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )

    assert not errors

    # 1 Present, 76 Missing
    assert election.progress == (1, 77)


def test_import_wabsti_majorz_regional(session):
    session.add(
        Election(
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

        errors = import_election_wabsti_majorz(
            election, principal_zg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'AnzMandate',
                        'BFS',
                        'StimmBer',
                        'StimmAbgegeben',
                        'StimmLeer',
                        'StimmUngueltig',
                        'KandName_1',
                        'Stimmen_1',
                        'KandName_2',
                        'Stimmen_2',
                    )),
                    ','.join((
                        '',
                        '1701',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                    ','.join((
                        '',
                        '1702',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

        errors = import_election_wabsti_majorz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'AnzMandate',
                        'BFS',
                        'StimmBer',
                        'StimmAbgegeben',
                        'StimmLeer',
                        'StimmUngueltig',
                        'KandName_1',
                        'Stimmen_1',
                        'KandName_2',
                        'Stimmen_2',
                    )),
                    ','.join((
                        '',
                        '3231',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                    ','.join((
                        '',
                        '3276',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert [error.error for error in errors] == expected

    # OK
    election.distinct = True
    errors = import_election_wabsti_majorz(
        election, principal_zg,
        BytesIO((
            '\n'.join((
                ','.join((
                    'AnzMandate',
                    'BFS',
                    'StimmBer',
                    'StimmAbgegeben',
                    'StimmLeer',
                    'StimmUngueltig',
                    'KandName_1',
                    'Stimmen_1',
                    'KandName_2',
                    'Stimmen_2',
                )),
                ','.join((
                    '',
                    '1701',
                    '100',
                    '90',
                    '1',
                    '1',
                    'Leere Zeilen',
                    '0',
                    'Ungültige Stimmen',
                    '1'
                )),
            ))
        ).encode('utf-8')), 'text/plain'
    )
    assert not errors
    assert election.progress == (1, 1)

    # Temporary
    for distinct, total in ((False, 1), (True, 13)):
        election.distinct = distinct

        errors = import_election_wabsti_majorz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'AnzMandate',
                        'BFS',
                        'StimmBer',
                        'StimmAbgegeben',
                        'StimmLeer',
                        'StimmUngueltig',
                        'KandName_1',
                        'Stimmen_1',
                        'KandName_2',
                        'Stimmen_2',
                    )),
                    ','.join((
                        '',
                        '3231',
                        '100',
                        '90',
                        '1',
                        '1',
                        'Leere Zeilen',
                        '0',
                        'Ungültige Stimmen',
                        '1'
                    )),
                ))
            ).encode('utf-8')), 'text/plain'
        )
        assert not errors
        assert election.progress == (1, total)
