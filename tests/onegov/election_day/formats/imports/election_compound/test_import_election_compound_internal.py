from __future__ import annotations

from datetime import date
from datetime import datetime
from freezegun import freeze_time
from io import BytesIO
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import export_election_compound_internal
from onegov.election_day.formats import import_election_compound_internal
from onegov.election_day.models import Canton
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from pytz import utc


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_internal_compound_regional_gr(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    results = import_test_datasets(
        api_format='internal',
        model='election_compound',
        principal='gr',
        domain='region',
        domain_segment=(
            'Alvaschein',
            'Avers',
            'Belfort',
            'Bergün',
            'Bregaglia',
            'Breil/Brigels',
            'Brusio',
            'Calanca',
            'Chur',
            'Churwalden',
            'Davos',
            'Disentis',
            'Domleschg',
            'Fünf Dörfer',
            'Ilanz',
            'Jenaz',
            'Klosters',
            'Küblis',
            'Lumnezia/Lugnez',
            'Luzein',
            'Maienfeld',
            'Mesocco',
            'Oberengadin',
            'Poschiavo',
            'Ramosch',
            'Rheinwald',
            'Rhäzüns',
            'Roveredo',
            'Safien',
            'Schams',
            'Schanfigg',
            'Schiers',
            'Seewis',
            'Suot Tasna',
            'Sur Tasna',
            'Surses',
            'Thusis',
            'Trins',
            'Val Müstair'
        ),
        domain_supersegment=39 * [''],
        number_of_mandates=(
            2,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            21,
            1,
            6,
            4,
            3,
            11,
            6,
            1,
            3,
            1,
            2,
            1,
            5,
            1,
            8,
            2,
            1,
            1,
            7,
            3,
            1,
            1,
            2,
            3,
            1,
            3,
            1,
            1,
            4,
            5,
            1,
        ),
        date_=date(2022, 5, 15),
        dataset_name='grossratswahlen-2022'
    )

    assert len(results) == 1
    election_compound, errors = next(iter(results.values()))
    assert not errors
    assert election_compound.last_result_change
    assert election_compound.completed
    assert election_compound.progress == (39, 39)
    assert election_compound.allocated_mandates == 120
    assert election_compound.number_of_mandates == 120
    assert len(election_compound.elected_candidates) == 120

    election = election_compound.elections[0]
    assert isinstance(election, ProporzElection)
    list_ = next((l for l in election.lists if l.name == 'FDP'))
    candidate = next((
        c for c in election.candidates if c.family_name == 'Crameri'
    ))
    result = next((r for r in list_.panachage_results if r.source_id is None))
    assert list_.votes == 360
    assert result.votes == 61
    assert candidate.votes == 659

    # roundtrip
    csv = convert_list_of_dicts_to_csv(
        export_election_compound_internal(
            election_compound, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    errors = import_election_compound_internal(
        election_compound, Canton(canton='gr'), BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election_compound.last_result_change
    assert election_compound.completed
    assert election_compound.progress == (39, 39)
    assert election_compound.allocated_mandates == 120
    assert election_compound.number_of_mandates == 120
    assert len(election_compound.elected_candidates) == 120

    election = election_compound.elections[0]
    assert isinstance(election, ProporzElection)
    list_ = next((l for l in election.lists if l.name == 'FDP'))
    candidate = next((
        c for c in election.candidates if c.family_name == 'Crameri'
    ))
    result = next((r for r in list_.panachage_results if r.source_id is None))
    assert list_.votes == 360
    assert result.votes == 61
    assert candidate.votes == 659


def test_import_internal_compound_missing_headers(session: Session) -> None:
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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        ("Missing columns: 'candidate_elected'")
    ]


def test_import_internal_compound_invalid_values(session: Session) -> None:
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
                        'list_color',
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
                        'candidate_party_color',
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
                        'x x x',  # list_id
                        '',  # list_color
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
                        '',  # candidate_party_color
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
                        '',  # list_color
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
                        '',  # candidate_party_color
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
                        '1',  # list_id
                        'xxx',  # list_color
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
                        'xxx',  # candidate_party_color
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
                        '',  # list_color
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
                        '',  # candidate_party_color
                    )),
                ))
                ).encode('utf-8')), 'text/plain',
    )
    assert sorted((e.line, e.error.interpolate()) for e in errors) == [  # type: ignore[attr-defined]
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: list_votes'),
        (2, 'Invalid status'),
        (2, 'Not an alphanumeric: list_id'),
        (3, 'Empty value: list_id'),
        (4, 'Invalid color: candidate_party_color'),
        (4, 'Invalid color: list_color'),
    ]


def test_import_internal_compound_expats(session: Session) -> None:
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

    for has_expats in (False, True):
        election_1.has_expats = has_expats
        election_2.has_expats = has_expats
        for entity_id in (9170, 0):
            raw_errors = import_election_compound_internal(
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
            errors = [e.error.interpolate() for e in raw_errors]  # type: ignore[attr-defined]

            if has_expats:
                assert errors == [
                    'This format does not support separate results for expats'
                ]
            else:
                assert not errors


def test_import_internal_compound_temporary_results(session: Session) -> None:
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
    assert election_1.results
    assert election_1.has_results
    assert election_1.last_result_change == datetime(2022, 1, 1, tzinfo=utc)
    assert election_2.progress == (0, 9)
    assert election_2.results
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
    assert election_1.results
    assert election_1.has_results
    assert election_1.last_result_change == datetime(2022, 1, 2, tzinfo=utc)
    assert election_2.progress == (0, 0)
    assert not election_2.results
    assert not election_2.has_results
    assert election_2.last_result_change == datetime(2022, 1, 2, tzinfo=utc)
