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
    assert election.last_result_change
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
    assert election.allocated_mandates() == 0


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
    assert election.last_result_change
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
    assert election.allocated_mandates() == 1
    assert election.elected_candidates == [('Paul', 'Rechsteiner')]


def test_import_wabsti_majorz_regional_sg(session, import_test_datasets):
    # - regional results from Rorschach the 25.09.2016
    principal = 'sg'
    # Test regional election
    election, errors = import_test_datasets(
        'wabsti',
        'election',
        principal,
        'district',
        election_type='majorz',
        number_of_mandates=1,
        date_=date(2016, 9, 25),
        domain_segment='Rorschach',
        dataset_name='RO-Kreisgericht-Rohrschach',
    )

    assert not errors
    assert election.last_result_change
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
    assert election.allocated_mandates() == 0


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
    assert election.last_result_change
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
    assert election.allocated_mandates() == 6
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

    def create_csv(results):
        lines = []
        lines.append((
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
        ))
        for entity_id in results:
            lines.append((
                '',  # AnzMandate
                str(entity_id),  # BFS
                '100',  # StimmBer
                '90',  # StimmAbgegeben
                '1',  # StimmLeer
                '1',  # StimmUngueltig
                'Leere Zeilen',  # KandName_1
                '0',  # Stimmen_1
                'Ungültige Stimmen',  # KandName_2
                '1'  # Stimmen_2
            ))

        return BytesIO(
            '\n'.join(
                (','.join(column for column in line)) for line in lines
            ).encode('utf-8')
        ), 'text/plain'

    session.add(
        Election(
            title='election',
            domain='region',
            date=date(2022, 2, 19),
            number_of_mandates=1
        )
    )
    session.flush()
    election = session.query(Election).one()

    # ZG, municipality, too many municipalitites
    principal = Canton(canton='zg')
    election.domain = 'municipality'
    election.domain_segment = 'Baar'
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((1701, 1702))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '1702 is not part of this election'
    ]

    # ZG, municipality, ok
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((1701,))
    )
    assert not errors
    assert election.progress == (1, 1)

    # ZG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((1701, 1702))
    )
    assert not errors
    assert election.progress == (2, 2)

    # SG, district, too many districts
    principal = Canton(canton='sg')
    election.domain = 'district'
    election.domain_segment = 'Werdenberg'
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((3271, 3201))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '3201 is not part of Werdenberg'
    ]

    # SG, district, ok
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((
            3271, 3272, 3273, 3274,  # 3275, 3276
        ))
    )
    assert not errors
    assert election.progress == (4, 6)

    # SG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((3271, 3201))
    )
    assert not errors
    assert election.progress == (2, 2)

    # GR, region, too many regions
    principal = Canton(canton='gr')
    election.domain = 'region'
    election.domain_segment = 'Ilanz'
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((3572, 3513))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '3513 is not part of Ilanz'
    ]

    # GR, region, ok
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((
            (3572, 3575, 3581, 3582)   # 3619, 3988
        ))
    )
    assert not errors
    assert election.progress == (4, 6)

    # GR, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_wabsti_majorz(
        election, principal,
        *create_csv((3572, 3513))
    )
    assert not errors
    assert election.progress == (2, 2)
