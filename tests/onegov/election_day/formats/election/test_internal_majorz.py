from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.models import Canton

from tests.onegov.election_day.common import create_principal


def test_import_internal_majorz_cantonal_zg(
        session, import_test_datasets):

    # - cantonal results from ZG from the 18.10.2015
    principal = 'zg'

    election, errors = import_test_datasets(
        'internal',
        'election',
        principal,
        'canton',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='staenderatswahl-2015',
        expats=False
    )
    assert not errors
    assert election.completed
    assert election.progress == (11, 11)
    assert election.absolute_majority == 18191
    assert election.eligible_voters == 73355
    assert election.accounted_ballots == 38710
    assert election.accounted_votes == 72761
    assert election.blank_ballots == 63
    assert election.invalid_ballots == 115
    assert round(election.turnout, 2) == 53.01
    assert election.allocated_mandates == 2
    assert sorted(election.elected_candidates) == [
        ('Joachim', 'Eder'), ('Peter', 'Hegglin')
    ]

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    errors = import_election_internal_majorz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.completed
    assert election.progress == (11, 11)
    assert election.absolute_majority == 18191
    assert election.eligible_voters == 73355
    assert election.accounted_ballots == 38710
    assert election.accounted_votes == 72761
    assert election.blank_ballots == 63
    assert election.invalid_ballots == 115
    assert round(election.turnout, 2) == 53.01
    assert election.allocated_mandates == 2
    assert sorted(election.elected_candidates) == [
        ('Joachim', 'Eder'), ('Peter', 'Hegglin')
    ]


def test_import_internal_majorz_regional_zg(session, import_test_datasets):

    # - regional results form Zug from the 24.06.2012

    principal = 'zg'

    election, errors = import_test_datasets(
        'internal',
        'election',
        principal,
        'region',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=1,
        dataset_name='friedensrichter-2012-06-24',
        expats=False
    )
    assert not errors
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3237
    assert election.eligible_voters == 16174
    assert election.blank_ballots == 89
    assert election.invalid_ballots == 72
    assert round(election.turnout, 2) == 41.02
    assert election.elected_candidates == [('Johannes', 'Stöckli')]

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    errors = import_election_internal_majorz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3237
    assert election.eligible_voters == 16174
    assert election.blank_ballots == 89
    assert election.invalid_ballots == 72
    assert round(election.turnout, 2) == 41.02
    assert election.elected_candidates == [('Johannes', 'Stöckli')]


def test_import_internal_majorz_municipality_bern(
        session, import_test_datasets):
    # Test communal election without quarters
    # - communal results from Bern from the 25.11.2015

    principal = 'bern'
    municipality = '1059'

    election, errors = import_test_datasets(
        'internal',
        'election',
        principal,
        'municipality',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=1,
        dataset_name='gemeinderat-2015-11-25',
        expats=False,
        municipality=municipality
    )
    assert not errors
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3294
    assert election.eligible_voters == 18699
    assert election.blank_ballots == 124
    assert election.invalid_ballots == 51
    assert round(election.turnout, 2) == 36.16
    assert election.allocated_mandates == 0
    assert election.candidates.count() == 4

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    errors = import_election_internal_majorz(
        election,
        create_principal(municipality=municipality),
        BytesIO(csv),
        'text/plain'
    )

    assert not errors
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3294
    assert election.eligible_voters == 18699
    assert election.blank_ballots == 124
    assert election.invalid_ballots == 51
    assert round(election.turnout, 2) == 36.16
    assert election.allocated_mandates == 0
    assert election.candidates.count() == 4


def test_import_internal_majorz_municipality_kriens(
        session, import_test_datasets):

    # Test communal election with quarters
    # communal results from Kriens from the 23.08.2015

    principal = 'kriens'
    municipality = '351'

    election, errors = import_test_datasets(
        'internal',
        'election',
        principal,
        'municipality',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=1,
        dataset_name='stadtpraesidiumswahl-2015-08-23',
        expats=False,
        municipality=municipality
    )
    assert not errors
    assert election.completed
    assert election.progress == (6, 6)
    assert election.absolute_majority == 12606
    assert election.eligible_voters == 82497
    assert election.blank_ballots == 1274
    assert election.invalid_ballots == 2797
    assert round(election.turnout, 2) == 35.49
    assert election.allocated_mandates == 1
    assert sorted(election.elected_candidates) == [('Tschäppät', 'Alexander')]

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    errors = import_election_internal_majorz(
        election,
        create_principal(municipality=municipality),
        BytesIO(csv),
        'text/plain'
    )

    assert not errors
    assert election.completed
    assert election.progress == (6, 6)
    assert election.absolute_majority == 12606
    assert election.eligible_voters == 82497
    assert election.blank_ballots == 1274
    assert election.invalid_ballots == 2797
    assert round(election.turnout, 2) == 35.49
    assert election.allocated_mandates == 1
    assert sorted(election.elected_candidates) == [('Tschäppät', 'Alexander')]


def test_import_internal_majorz_missing_headers(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_internal_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_absolute_majority',
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'candidate_family_name',
                    'candidate_first_name',
                    'candidate_id',
                    'candidate_votes',
                    'candidate_party',
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert [(e.error.interpolate()) for e in errors] == [
        ("Missing columns: 'candidate_elected'")
    ]


def test_import_internal_majorz_invalid_values(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='sg')

    errors = import_election_internal_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_absolute_majority',
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'candidate_family_name',
                    'candidate_first_name',
                    'candidate_id',
                    'candidate_elected',
                    'candidate_votes',
                    'candidate_party',
                )),
                ','.join((
                    'xxx',  # election_absolute_majority
                    'xxx',  # election_status
                    'xxx',  # entity_id
                    'xxx',  # entity_counted
                    'xxx',  # entity_eligible_voters
                    'xxx',  # entity_received_ballots
                    'xxx',  # entity_blank_ballots
                    'xxx',  # entity_invalid_ballots
                    'xxx',  # entity_blank_votes
                    'xxx',  # entity_invalid_votes
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    'xxx',  # candidate_id
                    'xxx',  # candidate_elected
                    'xxx',  # candidate_votes
                    'xxx',  # candidate_party
                )),
                ','.join((
                    '',  # election_absolute_majority
                    'unknown',  # election_status
                    '1234',  # entity_id
                    'True',  # entity_counted
                    '100',  # entity_eligible_voters
                    '10',  # entity_received_ballots
                    '0',  # entity_blank_ballots
                    '0',  # entity_invalid_ballots
                    '0',  # entity_blank_votes
                    '0',  # entity_invalid_votes
                    '',  # candidate_family_name
                    '',  # candidate_first_name
                    '',  # candidate_id
                    '',  # candidate_elected
                    '',  # candidate_votes
                    '',  # candidate_party
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    errors = sorted([(e.line, e.error.interpolate()) for e in errors])
    print(errors)
    assert errors == [
        (2, 'Invalid integer: candidate_id'),
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: election_absolute_majority'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid status'),
        (3, '1234 is unknown'),
    ]


def test_import_internal_majorz_expats(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='zg')

    for expats in (False, True):
        election.expats = expats
        for entity_id in (9170, 0):
            errors = import_election_internal_majorz(
                election, principal,
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'election_absolute_majority',
                            'election_status',
                            'entity_id',
                            'entity_counted',
                            'entity_eligible_voters',
                            'entity_received_ballots',
                            'entity_blank_ballots',
                            'entity_invalid_ballots',
                            'entity_blank_votes',
                            'entity_invalid_votes',
                            'candidate_family_name',
                            'candidate_first_name',
                            'candidate_id',
                            'candidate_elected',
                            'candidate_votes',
                            'candidate_party',
                        )),
                        ','.join((
                            '',  # election_absolute_majority
                            'unknown',  # election_status
                            str(entity_id),  # entity_id
                            'True',  # entity_counted
                            '111',  # entity_eligible_voters
                            '11',  # entity_received_ballots
                            '1',  # entity_blank_ballots
                            '1',  # entity_invalid_ballots
                            '1',  # entity_blank_votes
                            '1',  # entity_invalid_votes
                            'xxx',  # candidate_family_name
                            'xxx',  # candidate_first_name
                            '1',  # candidate_id
                            'false',  # candidate_elected
                            '1',  # candidate_votes
                            '',  # candidate_party
                        ))
                    ))
                ).encode('utf-8')), 'text/plain',
            )
            errors = [(e.line, e.error.interpolate()) for e in errors]
            result = election.results.filter_by(entity_id=0).first()
            if expats:
                assert errors == []
                assert result.invalid_votes == 1
            else:
                assert errors == [(None, 'No data found')]
                assert result is None


def test_import_internal_majorz_temporary_results(session):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=6,
        )
    )
    session.flush()
    election = session.query(Election).one()
    principal = Canton(canton='zg')

    errors = import_election_internal_majorz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_absolute_majority',
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'candidate_family_name',
                    'candidate_first_name',
                    'candidate_id',
                    'candidate_elected',
                    'candidate_votes',
                    'candidate_party',
                )),
                ','.join((
                    '',  # election_absolute_majority
                    'unknown',  # election_status
                    '1701',  # entity_id
                    'True',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    '',  # candidate_party
                )),
                ','.join((
                    '',  # election_absolute_majority
                    'unknown',  # election_status
                    '1702',  # entity_id
                    'False',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    '',  # candidate_party
                ))
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert not errors

    # 1 Counted, 1 Uncounted, 10 Missing
    assert election.progress == (1, 11)


def test_import_internal_majorz_regional(session):
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

        errors = import_election_internal_majorz(
            election, principal_zg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'election_absolute_majority',
                        'election_status',
                        'entity_id',
                        'entity_counted',
                        'entity_eligible_voters',
                        'entity_received_ballots',
                        'entity_blank_ballots',
                        'entity_invalid_ballots',
                        'entity_blank_votes',
                        'entity_invalid_votes',
                        'candidate_family_name',
                        'candidate_first_name',
                        'candidate_id',
                        'candidate_elected',
                        'candidate_votes',
                        'candidate_party',
                    )),
                    ','.join((
                        '',  # election_absolute_majority
                        'unknown',  # election_status
                        '1701',  # entity_id
                        'True',  # entity_counted
                        '111',  # entity_eligible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        '1',  # candidate_id
                        'false',  # candidate_elected
                        '1',  # candidate_votes
                        '',  # candidate_party
                    )),
                    ','.join((
                        '',  # election_absolute_majority
                        'unknown',  # election_status
                        '1702',  # entity_id
                        'False',  # entity_counted
                        '111',  # entity_eligible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        '1',  # candidate_id
                        'false',  # candidate_elected
                        '1',  # candidate_votes
                        '',  # candidate_party
                    ))
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert [error.error for error in errors] == expected

        errors = import_election_internal_majorz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'election_absolute_majority',
                        'election_status',
                        'entity_id',
                        'entity_counted',
                        'entity_eligible_voters',
                        'entity_received_ballots',
                        'entity_blank_ballots',
                        'entity_invalid_ballots',
                        'entity_blank_votes',
                        'entity_invalid_votes',
                        'candidate_family_name',
                        'candidate_first_name',
                        'candidate_id',
                        'candidate_elected',
                        'candidate_votes',
                        'candidate_party',
                    )),
                    ','.join((
                        '',  # election_absolute_majority
                        'unknown',  # election_status
                        '3231',  # entity_id
                        'True',  # entity_counted
                        '111',  # entity_eligible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        '1',  # candidate_id
                        'false',  # candidate_elected
                        '1',  # candidate_votes
                        '',  # candidate_party
                    )),
                    ','.join((
                        '',  # election_absolute_majority
                        'unknown',  # election_status
                        '3276',  # entity_id
                        'True',  # entity_counted
                        '111',  # entity_eligible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        '1',  # candidate_id
                        'false',  # candidate_elected
                        '1',  # candidate_votes
                        '',  # candidate_party
                    ))
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert [error.error for error in errors] == expected

    # OK
    election.distinct = True
    errors = import_election_internal_majorz(
        election, principal_zg,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_absolute_majority',
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'candidate_family_name',
                    'candidate_first_name',
                    'candidate_id',
                    'candidate_elected',
                    'candidate_votes',
                    'candidate_party',
                )),
                ','.join((
                    '',  # election_absolute_majority
                    'unknown',  # election_status
                    '1701',  # entity_id
                    'True',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    '',  # candidate_party
                ))
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert not errors
    assert election.progress == (1, 1)

    # Temporary
    for distinct, total in ((False, 1), (True, 13)):
        election.distinct = distinct

        errors = import_election_internal_majorz(
            election, principal_sg,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'election_absolute_majority',
                        'election_status',
                        'entity_id',
                        'entity_counted',
                        'entity_eligible_voters',
                        'entity_received_ballots',
                        'entity_blank_ballots',
                        'entity_invalid_ballots',
                        'entity_blank_votes',
                        'entity_invalid_votes',
                        'candidate_family_name',
                        'candidate_first_name',
                        'candidate_id',
                        'candidate_elected',
                        'candidate_votes',
                        'candidate_party',
                    )),
                    ','.join((
                        '',  # election_absolute_majority
                        'unknown',  # election_status
                        '3231',  # entity_id
                        'True',  # entity_counted
                        '111',  # entity_eligible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        '1',  # candidate_id
                        'false',  # candidate_elected
                        '1',  # candidate_votes
                        '',  # candidate_party
                    ))
                ))
            ).encode('utf-8')), 'text/plain',
        )
        assert not errors
        assert election.progress == (1, total)
