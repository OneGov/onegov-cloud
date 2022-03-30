from datetime import date
from datetime import datetime
from freezegun import freeze_time
from io import BytesIO
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.election_day.formats import import_election_compound_internal
from onegov.election_day.models import Canton
from pytz import utc


def test_import_internal_compound_missing_headers(session):
    election_1 = ProporzElection(
        title='election-1',
        domain='district',
        domain_segment='St. Gallen',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    election_2 = ProporzElection(
        title='election-2',
        domain='district',
        domain_segment='Rorschach',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    compound = ElectionCompound(
        title='election',
        domain='canton',
        domain_elections='district',
        date=date(2022, 10, 18),
    )
    session.add(election_1)
    session.add(election_2)
    session.add(compound)
    session.flush()
    compound.elections = [election_1, election_2]

    principal = Canton(canton='sg')

    errors = import_election_compound_internal(
        compound, principal,
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


def test_import_internal_compound_invalid_values(session):
    election_1 = ProporzElection(
        title='election-1',
        domain='district',
        domain_segment='St. Gallen',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    election_2 = ProporzElection(
        title='election-2',
        domain='district',
        domain_segment='Rorschach',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    compound = ElectionCompound(
        title='election',
        domain='canton',
        domain_elections='district',
        date=date(2022, 10, 18),
    )
    session.add(election_1)
    session.add(election_2)
    session.add(compound)
    session.flush()
    compound.elections = [election_1, election_2]

    principal = Canton(canton='sg')

    errors = import_election_compound_internal(
        compound, principal,
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
                    # St. Gallen
                    ','.join((
                        'unknown',  # election_status
                        '3201',  # entity_id
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
                    # Rorschach
                    ','.join((
                        'unknown',  # election_status
                        '3211',  # entity_id
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
                    # Rheintal
                    ','.join((
                        'unknown',  # election_status
                        '3235',  # entity_id
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
    errors = sorted([(e.line, e.error.interpolate()) for e in errors])
    assert errors == [
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: list_votes'),
        (2, 'Invalid status'),
        (2, 'Not an alphanumeric: list_id'),
        (3, 'Empty value: list_id'),
        (4, 'Empty value: list_id'),
    ]


def test_import_internal_compound_expats(session):
    election_1 = ProporzElection(
        title='election-1',
        domain='district',
        domain_segment='St. Gallen',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    election_2 = ProporzElection(
        title='election-2',
        domain='district',
        domain_segment='Rorschach',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    compound = ElectionCompound(
        title='election',
        domain='canton',
        domain_elections='district',
        date=date(2022, 10, 18),
    )
    session.add(election_1)
    session.add(election_2)
    session.add(compound)
    session.flush()
    compound.elections = [election_1, election_2]

    principal = Canton(canton='sg')

    for expats in (False, True):
        election_1.expats = expats
        election_2.expats = expats
        for entity_id in (9170, 0):
            errors = import_election_compound_internal(
                compound, principal,
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
            errors = [e.error.interpolate() for e in errors]

            if expats:
                assert errors == [
                    'This format does not support separate results for expats'
                ]
            else:
                assert not errors
                assert election_1.results.filter_by(entity_id=0).count() == 0
                assert election_2.results.filter_by(entity_id=0).count() == 0


def test_import_internal_compound_temporary_results(session):
    election_1 = ProporzElection(
        title='election-1',
        domain='district',
        domain_segment='St. Gallen',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    election_2 = ProporzElection(
        title='election-2',
        domain='district',
        domain_segment='Rorschach',
        date=date(2022, 10, 18),
        number_of_mandates=6,
    )
    compound = ElectionCompound(
        title='election',
        domain='canton',
        domain_elections='district',
        date=date(2022, 10, 18),
    )
    session.add(election_1)
    session.add(election_2)
    session.add(compound)
    session.flush()
    compound.elections = [election_1, election_2]

    assert compound.last_result_change is None
    assert election_1.last_result_change is None
    assert election_2.last_result_change is None

    principal = Canton(canton='sg')

    csv = '\n'.join((
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
        # St. Gallen
        ','.join((
            'unknown',  # election_status
            '3201',  # entity_id
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
        # Rorschach
        ','.join((
            'unknown',  # election_status
            '3211',  # entity_id
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
        )),
        # Rheintal (unused)
        ','.join((
            'unknown',  # election_status
            '3233',  # entity_id
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

    # Upload
    with freeze_time("2022-01-01"):
        errors = import_election_compound_internal(
            compound, principal,
            BytesIO(csv.encode('utf-8')), 'text/plain',
        )
        assert not errors

    assert compound.progress == (0, 2)
    assert compound.has_results
    assert compound.last_result_change == datetime(2022, 1, 1, tzinfo=utc)
    assert election_1.progress == (1, 9)
    assert election_1.results.first()
    assert election_1.has_results
    assert election_1.last_result_change == datetime(2022, 1, 1, tzinfo=utc)
    assert election_2.progress == (0, 9)
    assert election_2.results.first()
    assert not election_2.has_results
    assert election_2.last_result_change == datetime(2022, 1, 1, tzinfo=utc)

    # Upload only St. Gallen again
    with freeze_time("2022-01-02"):
        errors = import_election_compound_internal(
            compound, principal,
            BytesIO('\n'.join(csv.split()[:2]).encode('utf-8')), 'text/plain',
        )
        assert not errors

    assert compound.progress == (0, 2)
    assert compound.has_results
    assert compound.last_result_change == datetime(2022, 1, 2, tzinfo=utc)
    assert election_1.progress == (1, 9)
    assert election_1.results.first()
    assert election_1.has_results
    assert election_1.last_result_change == datetime(2022, 1, 2, tzinfo=utc)
    assert election_2.progress == (0, 0)
    assert not election_2.results.first()
    assert not election_2.has_results
    assert election_2.last_result_change == datetime(2022, 1, 2, tzinfo=utc)
