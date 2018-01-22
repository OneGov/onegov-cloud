import tarfile

from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.ballot import ProporzElection
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.models import Canton
from pytest import mark


@mark.parametrize("tar_file", [
    module_path('onegov.election_day',
                'tests/fixtures/internal_election.tar.gz'),
])
def test_import_internal_proporz(session, tar_file):
    session.add(
        ProporzElection(
            title='election',
            domain='canton',
            type='proporz',
            date=date(2015, 10, 18),
            number_of_mandates=2,
        )
    )
    session.flush()
    election = session.query(Election).one()

    principal = Canton(canton='zg')
    entities = principal.entities.get(election.date.year, {})

    # The tar file contains results from ZG from the 18.10.2015 (v1.13.1)
    # and results from Bern from the 25.11.2015 (v1.13.1)
    with tarfile.open(tar_file, 'r|gz') as f:
        f.extractfile(f.next()).read()
        csv_proporz = f.extractfile(f.next()).read()
        f.extractfile(f.next()).read()

    # Test federal proporz
    election.number_of_mandates = 3
    errors = import_election_internal_proporz(
        election, entities, BytesIO(csv_proporz), 'text/plain',
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 11
    assert election.total_entities == 11
    assert election.results.count() == 11
    assert election.absolute_majority is None
    assert election.elegible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert round(election.turnout, 2) == 53.74
    assert election.allocated_mandates == 3
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

    errors = import_election_internal_proporz(
        election, entities, BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.completed
    assert election.counted_entities == 11
    assert election.total_entities == 11
    assert election.results.count() == 11
    assert election.absolute_majority is None
    assert election.elegible_voters == 74803
    assert election.accounted_ballots == 39067
    assert election.accounted_votes == 116689
    assert election.blank_ballots == 118
    assert election.invalid_ballots == 1015
    assert round(election.turnout, 2) == 53.74
    assert election.allocated_mandates == 3
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
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_internal_proporz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_status',
                    'election_counted_entities',
                    'election_total_entities',
                    'entity_id',
                    'entity_elegible_voters',
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
    entities = principal.entities.get(election.date.year, {})

    errors = import_election_internal_proporz(
        election, entities,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_status',
                    'election_counted_entities',
                    'election_total_entities',
                    'entity_id',
                    'entity_elegible_voters',
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
                    'xxx',  # election_counted_entities
                    'xxx',  # election_total_entities
                    'xxx',  # entity_id
                    'xxx',  # entity_elegible_voters
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
                    '1',  # election_counted_entities
                    '78',  # election_total_entities
                    '1234',  # entity_id
                    '100',  # entity_elegible_voters
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

    assert sorted([(e.line, e.error.interpolate()) for e in errors]) == [
        (2, 'Invalid candidate results'),
        (2, 'Invalid candidate values'),
        (2, 'Invalid election values'),
        (2, 'Invalid entity values'),
        (2, 'Invalid list results'),
        (2, 'Invalid list results'),
        (2, 'Invalid list values'),
        (2, 'Invalid status'),
        (3, '1234 is unknown'),
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
    entities = principal.entities.get(election.date.year, {})

    for entity_id in (9170, 0):
        errors = import_election_internal_proporz(
            election, entities,
            BytesIO((
                '\n'.join((
                    ','.join((
                        'election_status',
                        'election_counted_entities',
                        'election_total_entities',
                        'entity_id',
                        'entity_elegible_voters',
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
                        '1',  # election_counted_entities
                        '11',  # election_total_entities
                        str(entity_id),  # entity_id
                        '111',  # entity_elegible_voters
                        '11',  # entity_received_ballots
                        '1',  # entity_blank_ballots
                        '1',  # entity_invalid_ballots
                        '1',  # entity_blank_votes
                        '1',  # entity_invalid_votes
                        '',  # list_name
                        '',  # list_id
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
        assert not errors
        assert election.results.filter_by(entity_id=0).one().invalid_votes == 1


# todo: test temporary results
