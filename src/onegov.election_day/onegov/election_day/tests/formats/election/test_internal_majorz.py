import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day',
                'tests/fixtures/internal_majorz.tar.gz'),
])
def test_import_internal_majorz(session, tar_file):
    session.add(
        Election(
            title='election',
            domain='canton',
            date=date(2015, 10, 18),
            number_of_mandates=2,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Canton(canton='zg')

    # The tar file contains
    # - cantonal results from ZG from the 18.10.2015
    # - regional results form Zug from the 24.06.2012
    # - communal results from Bern from the 25.11.2015
    # - communal results from Kriens from the 23.08.2015
    with tarfile.open(tar_file, 'r|gz') as f:
        csv_cantonal = f.extractfile(f.next()).read()
        csv_regional = f.extractfile(f.next()).read()
        csv_communal_1 = f.extractfile(f.next()).read()
        csv_communal_2 = f.extractfile(f.next()).read()

    # Test federal election
    errors = import_election_internal_majorz(
        election, principal, BytesIO(csv_cantonal), 'text/plain',
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
        election, principal, BytesIO(csv), 'text/plain'
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

    # Test regional election
    election.domain = 'region'
    election.number_of_mandates = 1

    errors = import_election_internal_majorz(
        election, principal, BytesIO(csv_regional), 'text/plain',
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
        election, principal, BytesIO(csv), 'text/plain'
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

    # Test communal election without quarters
    principal = Municipality(municipality='1059')

    election.domain = 'municipality'
    election.number_of_mandates = 1

    errors = import_election_internal_majorz(
        election, principal, BytesIO(csv_communal_1), 'text/plain',
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
        election, principal, BytesIO(csv), 'text/plain'
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

    # Test communal election with quarters
    principal = Municipality(municipality='351')

    errors = import_election_internal_majorz(
        election, principal, BytesIO(csv_communal_2), 'text/plain',
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
        election, principal, BytesIO(csv), 'text/plain'
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

    assert sorted([(e.line, e.error.interpolate()) for e in errors]) == [
        (2, 'Invalid candidate results'),
        (2, 'Invalid candidate values'),
        (2, 'Invalid election values'),
        (2, 'Invalid entity values'),
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
        assert not errors
        assert election.results.filter_by(entity_id=0).one().invalid_votes == 1


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
