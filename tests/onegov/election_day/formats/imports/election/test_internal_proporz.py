from __future__ import annotations

from datetime import date
from io import BytesIO
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import export_election_internal_proporz
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import create_principal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_internal_proporz_cantonal_zg(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    for roundtrip in (False, True):
        if not roundtrip:
            results = import_test_datasets(
                api_format='internal',
                model='election',
                principal='zg',
                domain='canton',
                election_type='proporz',
                number_of_mandates=3,
                date_=date(2015, 10, 18),
                dataset_name='nationalratswahlen-2015',
                has_expats=False
            )
            assert len(results) == 1
            election, errors = next(iter(results.values()))
        else:
            csv = convert_list_of_dicts_to_csv(
                export_election_internal_proporz(
                    election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
                )
            ).encode('utf-8')
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
        assert election.allocated_mandates == 3
        assert sorted(election.elected_candidates) == [
            ('Bruno', 'Pezzatti'), ('Gerhard', 'Pfister'), ('Thomas', 'Aeschi')
        ]
        assert sorted([list.votes for list in election.lists]) == [
            347, 575, 807, 1128, 1333, 1701, 2186, 3314, 4178, 4299, 4436,
            5844, 6521, 8868, 16285, 24335, 30532
        ]
        assert sorted([list.votes for list in election.list_connections]) == [
            0, 1128, 4178, 8352, 16048, 20584, 30856, 35543
        ]


def test_import_internal_proporz_cantonal_bl(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    for roundtrip in (False, True):
        if not roundtrip:
            results = import_test_datasets(
                api_format='internal',
                model='election',
                principal='bl',
                domain='canton',
                election_type='proporz',
                number_of_mandates=3,
                date_=date(2019, 10, 20),
                dataset_name='nationalratswahlen-2019',
                has_expats=False
            )
            assert len(results) == 1
            election, errors = next(iter(results.values()))
        else:
            csv = convert_list_of_dicts_to_csv(
                export_election_internal_proporz(
                    election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
                )
            ).encode('utf-8')
            principal = create_principal('bl')
            errors = import_election_internal_proporz(
                election, principal, BytesIO(csv), 'text/plain'
            )

        assert not errors
        assert election.last_result_change
        assert election.completed
        assert election.progress == (86, 86)
        assert election.absolute_majority is None
        assert election.accounted_ballots == 79241
        assert election.received_ballots == 80843
        assert election.blank_ballots == 94
        assert election.invalid_ballots == 1508
        assert election.allocated_mandates == 7
        assert sorted(election.elected_candidates) == [
            ('Daniela', 'Schneeberger'), ('Elisabeth', 'Schneider-Schneiter'),
            ('Eric', 'Nussbaumer'), ('Maya', 'Graf'), ('Samira', 'Marti'),
            ('Sandra', 'Sollberger'), ('Thomas', 'de Courten')
        ]
        assert sorted([list.votes for list in election.lists]) == [
            634, 1467, 2058, 2658, 2862, 3051, 3922, 4111, 4341, 4690, 5419,
            6158, 6470, 16074, 23337, 37974, 87578, 88885, 113689, 131564
        ]
        assert sorted([list.votes for list in election.list_connections]) == [
            0, 0, 6470, 19125, 28756, 46426, 90352, 98426, 119209, 137544
        ]
        lists = {list_.id: list_ for list_ in election.lists}
        list_ = next((l for l in election.lists if l.list_id == '01'))
        assert {
            lists[r.source_id].list_id if r.source_id else '00': r.votes
            for r in list_.panachage_results
        } == {
            '02': 1148,
            '03': 4751,
            '04': 225,
            '05': 1381,
            '06': 42,
            '07': 912,
            '08': 222,
            '11': 775,
            '12': 31,
            '13': 19,
            # '22': 0
            '23': 2,
            '33': 14,
            '34': 10,
            '44': 4,
            '55': 25,
            '56': 29,
            '70': 35,
            '77': 7,
            '00': 16051
        }
        candidate = next(
            (c for c in election.candidates if c.candidate_id == '0101')
        )
        result_id = next(
            (r for r in election.results if r.entity_id == 2761)
        ).id
        assert {
            lists[r.source_id].list_id if r.source_id else '00': r.votes
            for r in candidate.panachage_results
            if r.election_result_id == result_id
        } == {
            '01': 340,
            '02': 10,
            '03': 38,
            '04': 4,
            '05': 36,
            '07': 4,
            '08': 1,
            '11': 2,
            '33': 2,
            '00': 140
            # others are zero
        }


def test_import_internal_proporz_regional_zg(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # Test regional election

    principal = create_principal('zg')

    results = import_test_datasets(
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
    assert len(results) == 1
    election, errors = next(iter(results.values()))

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
    assert election.allocated_mandates == 19
    assert sorted([list.votes for list in election.lists]) == [
        1175, 9557, 15580, 23406, 23653, 27116, 31412
    ]

    # check panachage results
    assert election.party_panachage_results == []

    # check panachage result from list 3
    list_ = next((l for l in election.lists if l.list_id == '3'))
    assert list_.votes == 23653
    assert sum([p.votes for p in list_.panachage_results]) == (
        606 + 334 + 756 + 221 + 118 + 1048 + 2316
    )

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_proporz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

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
    assert election.allocated_mandates == 19
    assert sorted([list.votes for list in election.lists]) == [
        1175, 9557, 15580, 23406, 23653, 27116, 31412
    ]
    list_ = next((l for l in election.lists if l.list_id == '3'))
    assert list_.votes == 23653
    assert sum([p.votes for p in list_.panachage_results]) == (
        606 + 334 + 756 + 221 + 118 + 1048 + 2316
    )


def test_import_internal_proporz_missing_headers(session: Session) -> None:
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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        ("Missing columns: 'candidate_elected'")
    ]


def test_import_internal_proporz_invalid_values(session: Session) -> None:
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

    raw_errors = import_election_internal_proporz(
        election, principal,
        BytesIO((
                '\n'.join((
                    ','.join((
                        'election_status',
                        'entity_id',
                        'entity_counted',
                        'entity_eligible_voters',
                        'entity_expats',
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
                        'candidate_gender',
                        'candidate_year_of_birth',
                    )),
                    ','.join((
                        'xxx',  # election_status
                        'xxx',  # entity_id
                        'xxx',  # entity_counted
                        'xxx',  # entity_eligible_voters
                        '',  # entity_expats
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
                        '',  # candidate_gender
                        '',  # candidate_year_of_birth
                    )),
                    ','.join((
                        'unknown',  # election_status
                        '1234',  # entity_id
                        'True',  # entity_counted
                        '100',  # entity_eligible_voters
                        '30',  # entity_expats
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
                        'xxx',  # candidate_gender
                        '',  # candidate_year_of_birth
                    )),
                    ','.join((
                        'unknown',  # election_status
                        '3251',  # entity_id
                        'True',  # entity_counted
                        '100',  # entity_eligible_voters
                        'xxx',  # entity_expats
                        '10',  # entity_received_ballots
                        '0',  # entity_blank_ballots
                        '0',  # entity_invalid_ballots
                        '0',  # entity_blank_votes
                        '0',  # entity_invalid_votes
                        '',  # list_name
                        '1',  # list_id
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
                        '',  # candidate_gender
                        'xxx',  # candidate_year_of_birth
                    )),
                    ','.join((
                        'unknown',  # election_status
                        '3251',  # entity_id
                        'True',  # entity_counted
                        '100',  # entity_eligible_voters
                        '30',  # entity_expats
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
                        '',  # candidate_gender
                        '',  # candidate_year_of_birth
                    )),
                ))
                ).encode('utf-8')), 'text/plain',
    )
    errors = sorted((e.line, e.error.interpolate()) for e in raw_errors)  # type: ignore[attr-defined]
    assert errors == [
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid integer: list_votes'),
        (2, 'Invalid status'),
        (2, 'Not an alphanumeric: list_id'),
        (2, 'Not an alphanumeric: list_id'),
        (3, '1234 is unknown'),
        (3, 'Empty value: list_id'),
        (3, 'Empty value: list_id'),
        (3, 'Invalid gender: xxx'),
        (4, 'Invalid integer: candidate_year_of_birth'),
        (4, 'Invalid integer: entity_expats'),
        (5, 'Invalid color: candidate_party_color'),
        (5, 'Invalid color: list_color'),
    ]


def test_import_internal_proporz_expats(session: Session) -> None:
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

    for has_expats in (False, True):
        election.has_expats = has_expats
        for entity_id in (9170, 0):
            raw_errors = import_election_internal_proporz(
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
            errors = [(e.line, e.error.interpolate()) for e in raw_errors]  # type: ignore[attr-defined]
            result = next(
                (r for r in election.results if r.entity_id == 0), None
            )
            if has_expats:
                assert errors == []
                assert result is not None
                assert result.invalid_votes == 1
            else:
                assert errors == [(None, 'No data found')]
                assert result is None


def test_import_internal_proporz_temporary_results(session: Session) -> None:
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
    assert isinstance(election, ProporzElection)
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
                    '1',  # list_votes
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
                    '10.5',  # list_id
                    '',  # list_number_of_mandates
                    '1',  # list_votes
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

    # 1 Counted, 1 Uncounted, 10 Missing
    assert election.progress == (1, 11)
    assert election.eligible_voters == 111
    assert election.expats == 0
    assert election.received_ballots == 11
    assert election.blank_ballots == 1
    assert election.invalid_ballots == 1
    assert election.accounted_votes == 52
    assert election.lists[0].votes == 1
    assert election.candidates[0].votes == 1


def test_import_internal_proporz_regional(session: Session) -> None:

    def create_csv(
        results: tuple[tuple[int, bool], ...]
    ) -> tuple[BytesIO, str]:
        lines = [
            (
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
            ),
            *(
                (
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
                ) for entity_id, counted in results
            )
        ]

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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '1702 is not part of this business'
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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
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


def test_import_internal_proporz_panachage(session: Session) -> None:

    def create_csv(
        lheaders: list[str],
        cheaders: list[str],
        results: list[tuple[str, str, list[str]]]
    ) -> tuple[BytesIO, str]:
        lines = [
            (
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
                *(
                    f'list_panachage_votes_from_list_{h}'
                    for h in lheaders
                ),
                *(
                    f'candidate_panachage_votes_from_list_{h}'
                    for h in cheaders
                ),
            ),
            *(
                (
                    'unknown',  # election_status
                    entity_id,  # entity_id
                    'True',  # entity_counted
                    '111',  # entity_eligible_voters
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    candidate_id,  # list_name
                    candidate_id,  # list_id
                    '',  # list_number_of_mandates
                    '',  # list_votes
                    '',  # list_connection
                    '',  # list_connection_parent
                    candidate_id,  # candidate_family_name
                    'xxx',  # candidate_first_name
                    candidate_id,  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    '',  # candidate_party
                    *panachage,
                )
                for candidate_id, entity_id, panachage in results
            )
        ]

        return BytesIO(
            '\n'.join(
                (','.join(column for column in line)) for line in lines
            ).encode('utf-8')
        ), 'text/plain'

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
    lquery = session.query(ListPanachageResult)
    cquery = session.query(CandidatePanachageResult)

    # No panachage results
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            [], [],
            [('1', '3271', [])]
        )
    )
    assert not errors
    assert lquery.count() == 0
    assert cquery.count() == 0

    # Irrelevant panchage headers are ignored
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            ['10', '11'], ['10', '11'],
            [
                ('1', '3271', ['', '', '', ''])
            ]
        )
    )

    assert not errors
    assert lquery.count() == 0
    assert cquery.count() == 0

    # Missing list data and data with source == target is ignored, all other
    # data is parsed correctly
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            ['1', '2', '3', '999'], [],
            [
                ('1', '3271', ['1', '', '3', '']),
                ('2', '3271', ['4', '5', '', '']),
                ('3', '3271', ['', '8', '9', '999']),
            ]
        )
    )
    list_ids = dict(session.query(List.list_id, List.id))
    list_ids['999'] = None
    assert not errors
    assert lquery.count() == 4
    assert lquery.filter_by(source_id=list_ids['1']).one().votes == 4
    assert lquery.filter_by(source_id=list_ids['2']).one().votes == 8
    assert lquery.filter_by(source_id=list_ids['3']).one().votes == 3
    assert lquery.filter_by(source_id=list_ids['999']).one().votes == 999
    assert cquery.count() == 0

    # Later diverging list panachage results are ignored
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            ['1', '2', '3', '999'], [],
            [
                ('1', '3271', ['1', '', '3', '']),
                ('2', '3271', ['4', '5', '', '']),
                ('3', '3271', ['', '8', '9', '999']),
                ('1', '3272', ['10', '', '30', '']),
                ('2', '3272', ['40', '50', '', '']),
                ('3', '3272', ['', '80', '90', '9990']),
            ]
        )
    )
    list_ids = dict(session.query(List.list_id, List.id))
    list_ids['999'] = None
    assert not errors
    assert lquery.count() == 4
    assert lquery.filter_by(source_id=list_ids['1']).one().votes == 4
    assert lquery.filter_by(source_id=list_ids['2']).one().votes == 8
    assert lquery.filter_by(source_id=list_ids['3']).one().votes == 3
    assert lquery.filter_by(source_id=list_ids['999']).one().votes == 999
    assert cquery.count() == 0

    # Missing candidate data is ignored, all other data is parsed correctly and
    # missing list data is aggregated
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            [], ['1', '2', '3', '999'],
            [
                ('1', '3271', ['1', '', '3', '']),
                ('2', '3271', ['4', '5', '', '']),
                ('3', '3271', ['', '8', '9', '999']),
                ('1', '3272', ['10', '', '30', '']),
                ('2', '3272', ['40', '50', '', '']),
                ('3', '3272', ['', '80', '90', '9990']),
            ]
        )
    )
    result_ids = dict(
        session.query(ElectionResult.entity_id, ElectionResult.id)
    )
    list_ids = dict(session.query(List.list_id, List.id))
    list_ids['999'] = None
    candidate_ids = dict(session.query(Candidate.candidate_id, Candidate.id))
    assert not errors
    assert cquery.count() == 14
    for candidate_id, result_id, list_id, votes in (
        ('1', 3271, '1', 1),
        ('1', 3271, '3', 3),
        ('1', 3272, '1', 10),
        ('1', 3272, '3', 30),
        ('2', 3271, '1', 4),
        ('2', 3271, '2', 5),
        ('2', 3272, '1', 40),
        ('2', 3272, '2', 50),
        ('3', 3271, '2', 8),
        ('3', 3271, '3', 9),
        ('3', 3271, '999', 999),
        ('3', 3272, '2', 80),
        ('3', 3272, '3', 90),
        ('3', 3272, '999', 9990),
    ):
        assert cquery.filter_by(
            target_id=candidate_ids[candidate_id],
            election_result_id=result_ids[result_id],
            source_id=list_ids[list_id]
        ).one().votes == votes
    assert lquery.count() == 4
    assert lquery.filter_by(source_id=list_ids['1']).one().votes == 44
    assert lquery.filter_by(source_id=list_ids['2']).one().votes == 88
    assert lquery.filter_by(source_id=list_ids['3']).one().votes == 33
    assert lquery.filter_by(source_id=list_ids['999']).one().votes == 10989

    # List panachage data with missing lists throws an error
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            ['1', '2', '3', '999'], [],
            [
                ('1', '3271', ['1', '2', '3', '999']),
                ('2', '3271', ['4', '5', '6', '999']),
            ]
        )
    )
    assert {e.error.interpolate() for e in errors} == {  # type: ignore[attr-defined]
        "Panachage results id 3 not in list_id's"
    }

    # Candidate panachage data with missing lists throws an error
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            [], ['1', '2', '3', '999'],
            [
                ('1', '3271', ['1', '2', '3', '999']),
                ('2', '3271', ['4', '5', '6', '999']),
            ]
        )
    )
    assert {e.error.interpolate() for e in errors} == {  # type: ignore[attr-defined]
        "Panachage results id 3 not in list_id's"
    }

    # Alphanumerical list_ids are also valid
    errors = import_election_internal_proporz(
        election, principal,
        *create_csv(
            ['eins', 'zwei.drei', 'vier_fuenf', '999'], [],
            [
                ('eins', '3271', ['1', '', '3', '']),
                ('zwei.drei', '3271', ['4', '5', '', '']),
                ('vier_fuenf', '3271', ['', '8', '9', '999']),
            ]
        )
    )
    list_ids = dict(session.query(List.list_id, List.id))
    list_ids['999'] = None
    assert not errors
    assert lquery.count() == 4
    assert lquery.filter_by(source_id=list_ids['eins']).one().votes == 4
    assert lquery.filter_by(source_id=list_ids['zwei.drei']).one().votes == 8
    assert lquery.filter_by(source_id=list_ids['vier_fuenf']).one().votes == 3
    assert cquery.count() == 0


def test_import_internal_proproz_optional_columns(session: Session) -> None:
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

    errors = import_election_internal_proporz(
        election, principal,
        BytesIO((
            '\n'.join((
                ','.join((
                    'election_status',
                    'entity_id',
                    'entity_counted',
                    'entity_eligible_voters',
                    'entity_expats',
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
                    'candidate_gender',
                    'candidate_year_of_birth',
                )),
                ','.join((
                    'unknown',  # election_status
                    '1701',  # entity_id
                    'True',  # entity_counted
                    '111',  # entity_eligible_voters
                    '30',  # entity_expats
                    '11',  # entity_received_ballots
                    '1',  # entity_blank_ballots
                    '1',  # entity_invalid_ballots
                    '1',  # entity_blank_votes
                    '1',  # entity_invalid_votes
                    'JFDP',  # list_name
                    '10.5',  # list_id
                    '#112233',  # list_color
                    '',  # list_number_of_mandates
                    '',  # list_votes
                    '',  # list_connection
                    '',  # list_connection_parent
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    'FDP',  # candidate_party
                    '#123456',  # candidate_party_color
                    'female',  # candidate_gender
                    '1970',  # candidate_year_of_birth
                ))
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert not errors
    assert election.candidates[0].gender == 'female'
    assert election.candidates[0].year_of_birth == 1970
    result = next((r for r in election.results if r.entity_id == 1701))
    assert result.expats == 30
    assert election.colors == {'FDP': '#123456', 'JFDP': '#112233'}
