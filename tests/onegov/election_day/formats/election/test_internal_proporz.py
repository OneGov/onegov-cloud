from datetime import date
from io import BytesIO
from onegov.ballot import Election, PanachageResult
from onegov.ballot import ProporzElection
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.models import Canton

from tests.onegov.election_day.common import print_errors, create_principal


def test_import_internal_proporz_cantonal(session, import_test_datasets):

    election, errors = import_test_datasets(
        api_format='internal',
        model='election',
        principal='zg',
        domain='canton',
        election_type='proporz',
        number_of_mandates=3,
        date_=date(2015, 10, 18),
        dataset_name='nationalratswahlen-2015',
        expats=False
    )
    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (11, 11)
    assert election.absolute_majority is None
    assert election.eligible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert round(election.turnout, 2) == 53.74
    assert election.allocated_mandates() == 3
    assert sorted(election.elected_candidates) == [
        ('Bruno', 'Pezzatti'), ('Gerhard', 'Pfister'), ('Thomas', 'Aeschi')
    ]
    assert sorted([list.votes for list in election.lists]) == [
        347, 575, 807, 1128, 1333, 1701, 2186, 3314, 4178, 4299, 4436, 5844,
        6521, 8868, 16285, 24335, 30532
    ]
    assert sorted([list.votes for list in election.list_connections]) == [
        0, 1128, 4178, 8352, 16048, 20584, 30856, 35543
    ]

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    principal = create_principal('zg')

    errors = import_election_internal_proporz(
        election, principal, BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (11, 11)
    assert election.absolute_majority is None
    assert election.eligible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert round(election.turnout, 2) == 53.74
    assert election.allocated_mandates() == 3
    assert sorted(election.elected_candidates) == [
        ('Bruno', 'Pezzatti'), ('Gerhard', 'Pfister'), ('Thomas', 'Aeschi')
    ]
    assert sorted([list.votes for list in election.lists]) == [
        347, 575, 807, 1128, 1333, 1701, 2186, 3314, 4178, 4299, 4436, 5844,
        6521, 8868, 16285, 24335, 30532
    ]
    assert sorted([list.votes for list in election.list_connections]) == [
        0, 1128, 4178, 8352, 16048, 20584, 30856, 35543
    ]


def test_import_internal_proporz_regional_zg(session, import_test_datasets):
    # Test regional election

    principal = create_principal('zg')

    election, errors = import_test_datasets(
        api_format='internal',
        model='election',
        principal='zg',
        domain='municipality',
        domain_segment='Zug',
        election_type='proporz',
        number_of_mandates=19,
        date_=date(2015, 10, 18),
        dataset_name='kantonsratswahl-2014'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority is None
    assert election.eligible_voters == 16481
    assert election.received_ballots == 7471
    assert election.blank_ballots == 59
    assert election.invalid_ballots == 204
    assert election.accounted_votes == 131899
    assert round(election.turnout, 2) == 45.33
    assert election.allocated_mandates() == 19
    assert sorted([list.votes for list in election.lists]) == [
        1175, 9557, 15580, 23406, 23653, 27116, 31412
    ]

    # check panachage result from list 3
    test_list = election.lists.first()
    assert test_list.list_id == '3'
    list_csv_votes = 23653
    votes_panachage_csv = 606 + 334 + 756 + 221 + 118 + 1048 + 2316
    assert test_list.votes == list_csv_votes

    panachage_results = session.query(PanachageResult)
    panachage_results = panachage_results.filter_by(owner=election.id).all()
    assert not panachage_results, 'Owner of lists pana results must be NULL'

    panachage_results = election.panachage_results

    for pa_result in panachage_results:
        assert len(pa_result.target) > 10, 'target must be a casted uuid'

    panachge_vote_count = 0
    for result in test_list.panachage_results:
        panachge_vote_count += result.votes
    assert panachge_vote_count == votes_panachage_csv

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(election.export()).encode('utf-8')

    errors = import_election_internal_proporz(
        election, principal, BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority is None
    assert election.eligible_voters == 16481
    assert election.received_ballots == 7471
    assert election.blank_ballots == 59
    assert election.invalid_ballots == 204
    assert election.accounted_votes == 131899
    assert round(election.turnout, 2) == 45.33
    assert election.allocated_mandates() == 19
    assert sorted([list.votes for list in election.lists]) == [
        1175, 9557, 15580, 23406, 23653, 27116, 31412
    ]


def test_import_internal_proporz_missing_headers(session):
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

    errors = import_election_internal_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'list_name',
                    'list_id',
                    'list_number_of_mandates',
                    'list_votes',
                    'list_connection',
                    'list_connection_parent',
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


def test_import_internal_proporz_invalid_values(session):
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

    errors = import_election_internal_proporz(
        election, principal,
        BytesIO((
                '\n'.join((
                    ','.join((
                        'election_status',
                        'entity_id',
                        'entity_counted',
                        'entity_eligible_voters',
                        'entity_received_ballots',
                        'entity_blank_ballots',
                        'entity_invalid_ballots',
                        'entity_blank_votes',
                        'entity_invalid_votes',
                        'list_name',
                        'list_id',
                        'list_number_of_mandates',
                        'list_votes',
                        'list_connection',
                        'list_connection_parent',
                        'candidate_family_name',
                        'candidate_first_name',
                        'candidate_id',
                        'candidate_elected',
                        'candidate_votes',
                        'candidate_party',
                    )),
                    ','.join((
                        'xxx',  # election_status
                        'xxx',  # entity_id
                        'xxx',  # entity_counted
                        'xxx',  # entity_eligible_voters
                        'xxx',  # entity_received_ballots
                        'xxx',  # entity_blank_ballots
                        'xxx',  # entity_invalid_ballots
                        'xxx',  # entity_blank_votes
                        'xxx',  # entity_invalid_votes
                        'xxx',  # list_name
                        'xxx',  # list_id
                        'xxx',  # list_number_of_mandates
                        'xxx',  # list_votes
                        'xxx',  # list_connection
                        'xxx',  # list_connection_parent
                        'xxx',  # candidate_family_name
                        'xxx',  # candidate_first_name
                        'xxx',  # candidate_id
                        'xxx',  # candidate_elected
                        'xxx',  # candidate_votes
                        'xxx',  # candidate_party
                    )),
                    ','.join((
                        'unknown',  # election_status
                        '1234',  # entity_id
                        'True',  # entity_counted
                        '100',  # entity_eligible_voters
                        '10',  # entity_received_ballots
                        '0',  # entity_blank_ballots
                        '0',  # entity_invalid_ballots
                        '0',  # entity_blank_votes
                        '0',  # entity_invalid_votes
                        '',  # list_name
                        '',  # list_id
                        '',  # list_number_of_mandates
                        '',  # list_votes
                        '',  # list_connection
                        '',  # list_connection_parent
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
    print_errors(errors)
    errors = sorted([(e.line, e.error.interpolate()) for e in errors])
    assert errors == [
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: list_votes'),
        (2, 'Invalid status'),
        (2, 'Not an alphanumeric: list_id'),
        (2, 'Not an alphanumeric: list_id'),    #
        (3, '1234 is unknown'),
        (3, 'Empty value: list_id'),
        (3, 'Empty value: list_id'),
    ]


def test_import_internal_proporz_expats(session):
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
    principal = Canton(canton='zg')

    for expats in (False, True):
        election.expats = expats
        for entity_id in (9170, 0):
            errors = import_election_internal_proporz(
                election, principal,
                BytesIO((
                    '\n'.join((
                        ','.join((
                            'election_status',
                            'entity_id',
                            'entity_counted',
                            'entity_eligible_voters',
                            'entity_received_ballots',
                            'entity_blank_ballots',
                            'entity_invalid_ballots',
                            'entity_blank_votes',
                            'entity_invalid_votes',
                            'list_name',
                            'list_id',
                            'list_number_of_mandates',
                            'list_votes',
                            'list_connection',
                            'list_connection_parent',
                            'candidate_family_name',
                            'candidate_first_name',
                            'candidate_id',
                            'candidate_elected',
                            'candidate_votes',
                            'candidate_party',
                        )),
                        ','.join((
                            'unknown',  # election_status
                            str(entity_id),  # entity_id
                            'True',  # entity_counted
                            '111',  # entity_eligible_voters
                            '11',  # entity_received_ballots
                            '1',  # entity_blank_ballots
                            '1',  # entity_invalid_ballots
                            '1',  # entity_blank_votes
                            '1',  # entity_invalid_votes
                            '',  # list_name
                            '10.5',  # list_id
                            '',  # list_number_of_mandates
                            '',  # list_votes
                            '',  # list_connection
                            '',  # list_connection_parent
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


def test_import_internal_proporz_temporary_results(session):
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
    principal = Canton(canton='zg')

    errors = import_election_internal_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_received_ballots',
                    'entity_blank_ballots',
                    'entity_invalid_ballots',
                    'entity_blank_votes',
                    'entity_invalid_votes',
                    'list_name',
                    'list_id',
                    'list_number_of_mandates',
                    'list_votes',
                    'list_connection',
                    'list_connection_parent',
                    'candidate_family_name',
                    'candidate_first_name',
                    'candidate_id',
                    'candidate_elected',
                    'candidate_votes',
                    'candidate_party',
                )),
                ','.join((
                    'unknown',  # election_status
                    '1701',  # entity_id
                    'True',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    '',  # list_name
                    '10.5',  # list_id
                    '',  # list_number_of_mandates
                    '',  # list_votes
                    '',  # list_connection
                    '',  # list_connection_parent
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    '',  # candidate_party
                )),
                ','.join((
                    'unknown',  # election_status
                    '1702',  # entity_id
                    'False',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    '',  # list_name
                    '03B.04',  # list_id
                    '',  # list_number_of_mandates
                    '',  # list_votes
                    '',  # list_connection
                    '',  # list_connection_parent
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
    print_errors(errors)
    assert not errors

    # 1 Counted, 1 Uncounted, 10 Missing
    assert election.progress == (1, 11)


def test_import_internal_proporz_regional(session):

    def create_csv(results):
        lines = []
        lines.append((
            'election_status',
            'entity_id',
            'entity_counted',
            'entity_eligible_voters',
            'entity_received_ballots',
            'entity_blank_ballots',
            'entity_invalid_ballots',
            'entity_blank_votes',
            'entity_invalid_votes',
            'list_name',
            'list_id',
            'list_number_of_mandates',
            'list_votes',
            'list_connection',
            'list_connection_parent',
            'candidate_family_name',
            'candidate_first_name',
            'candidate_id',
            'candidate_elected',
            'candidate_votes',
            'candidate_party',
        ))
        for entity_id, counted in results:
            lines.append((
                'unknown',  # election_status
                str(entity_id),  # entity_id
                str(counted),  # entity_counted
                '111',  # entity_eligible_voters
                '11',  # entity_received_ballots
                '1',  # entity_blank_ballots
                '1',  # entity_invalid_ballots
                '1',  # entity_blank_votes
                '1',  # entity_invalid_votes
                '',  # list_name
                '10.04',  # list_id
                '',  # list_number_of_mandates
                '',  # list_votes
                '',  # list_connection
                '',  # list_connection_parent
                'xxx',  # candidate_family_name
                'xxx',  # candidate_first_name
                '1',  # candidate_id
                'false',  # candidate_elected
                '1',  # candidate_votes
                '',  # candidate_party
            ))

        return BytesIO(
            '\n'.join(
                (','.join(column for column in line)) for line in lines
            ).encode('utf-8')
        ), 'text/plain'

    session.add(
        ProporzElection(
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
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((1701, False), (1702, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '1702 is not part of this election'
    ]

    # ZG, municipality, ok
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((1701, False),))
    )
    assert not errors
    assert election.progress == (0, 1)

    # ZG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((1701, True), (1702, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # SG, district, too many districts
    principal = Canton(canton='sg')
    election.domain = 'district'
    election.domain_segment = 'Werdenberg'
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((3271, False), (3201, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '3201 is not part of Werdenberg'
    ]

    # SG, district, ok
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv((
            (3271, True), (3272, False), (3273, False), (3274, False),
            # (3275, False), (3276, False)
        ))
    )
    assert not errors
    assert election.progress == (1, 6)

    # SG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((3271, True), (3201, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # GR, region, too many regions
    principal = Canton(canton='gr')
    election.domain = 'region'
    election.domain_segment = 'Ilanz'
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [
        '3513 is not part of Ilanz'
    ]

    # GR, region, ok
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv((
            (3572, True), (3575, False), (3581, False), (3582, False)
            # (3619, False), (3988, False)
        ))
    )
    assert not errors
    assert election.progress == (1, 6)

    # GR, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert not errors
    assert election.progress == (1, 2)
