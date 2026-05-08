from __future__ import annotations

from datetime import date
from io import BytesIO
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.election_day.formats import export_election_internal_majorz
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from tests.onegov.election_day.common import create_principal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.onegov.election_day.conftest import ImportTestDatasets


def test_import_internal_majorz_cantonal_zg(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    # - cantonal results from ZG from the 18.10.2015
    principal = 'zg'

    results = import_test_datasets(
        'internal',
        'election',
        principal,
        'canton',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=2,
        dataset_name='staenderatswahl-2015',
        has_expats=False
    )
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    assert election.last_result_change
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
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_majorz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    errors = import_election_internal_majorz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.last_result_change
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


def test_import_internal_majorz_regional_zg(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    # - regional results form Zug from the 24.06.2012
    principal = 'zg'

    results = import_test_datasets(
        'internal',
        'election',
        principal,
        'municipality',
        'majorz',
        date_=date(2015, 10, 18),
        domain_segment='Baar',
        number_of_mandates=1,
        dataset_name='friedensrichter-2012-06-24',
        has_expats=False
    )
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3237
    assert election.eligible_voters == 16174
    assert election.blank_ballots == 89
    assert election.invalid_ballots == 72
    assert round(election.turnout, 2) == 41.02
    assert election.elected_candidates == [('Johannes', 'Stöckli')]

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_majorz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    errors = import_election_internal_majorz(
        election, create_principal(principal), BytesIO(csv), 'text/plain'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3237
    assert election.eligible_voters == 16174
    assert election.blank_ballots == 89
    assert election.invalid_ballots == 72
    assert round(election.turnout, 2) == 41.02
    assert election.elected_candidates == [('Johannes', 'Stöckli')]


def test_import_internal_majorz_municipality_bern(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:
    # Test communal election without quarters
    # - communal results from Bern from the 25.11.2015

    principal = 'bern'
    municipality = '1059'

    results = import_test_datasets(
        'internal',
        'election',
        principal,
        'municipality',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=1,
        dataset_name='gemeinderat-2015-11-25',
        has_expats=False,
        municipality=municipality
    )
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3294
    assert election.eligible_voters == 18699
    assert election.blank_ballots == 124
    assert election.invalid_ballots == 51
    assert round(election.turnout, 2) == 36.16
    assert election.allocated_mandates == 0
    assert len(election.candidates) == 4

    # ... roundtrip
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_majorz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    errors = import_election_internal_majorz(
        election,
        create_principal(municipality=municipality),
        BytesIO(csv),
        'text/plain'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (1, 1)
    assert election.absolute_majority == 3294
    assert election.eligible_voters == 18699
    assert election.blank_ballots == 124
    assert election.invalid_ballots == 51
    assert round(election.turnout, 2) == 36.16
    assert election.allocated_mandates == 0
    assert len(election.candidates) == 4


def test_import_internal_majorz_municipality_kriens(
    session: Session,
    import_test_datasets: ImportTestDatasets
) -> None:

    # Test communal election with quarters
    # communal results from Kriens from the 23.08.2015

    principal = 'kriens'
    municipality = '351'

    results = import_test_datasets(
        'internal',
        'election',
        principal,
        'municipality',
        'majorz',
        date_=date(2015, 10, 18),
        number_of_mandates=1,
        dataset_name='stadtpraesidiumswahl-2015-08-23',
        has_expats=False,
        municipality=municipality
    )
    assert len(results) == 1
    election, errors = next(iter(results.values()))
    assert not errors
    assert election.last_result_change
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
    csv = convert_list_of_dicts_to_csv(
        export_election_internal_majorz(
            election, ['de_CH', 'fr_CH', 'it_CH', 'rm_CH']
        )
    ).encode('utf-8')

    errors = import_election_internal_majorz(
        election,
        create_principal(municipality=municipality),
        BytesIO(csv),
        'text/plain'
    )

    assert not errors
    assert election.last_result_change
    assert election.completed
    assert election.progress == (6, 6)
    assert election.absolute_majority == 12606
    assert election.eligible_voters == 82497
    assert election.blank_ballots == 1274
    assert election.invalid_ballots == 2797
    assert round(election.turnout, 2) == 35.49
    assert election.allocated_mandates == 1
    assert sorted(election.elected_candidates) == [('Tschäppät', 'Alexander')]


def test_import_internal_majorz_missing_headers(session: Session) -> None:
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
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        ("Missing columns: 'candidate_elected'")
    ]


def test_import_internal_majorz_invalid_values(session: Session) -> None:
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
                    'entity_expats',
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
                    'candidate_party_color',
                    'candidate_gender',
                    'candidate_year_of_birth',
                )),
                ','.join((
                    'xxx',  # election_absolute_majority
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
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    'xxx',  # candidate_id
                    'xxx',  # candidate_elected
                    'xxx',  # candidate_votes
                    'xxx',  # candidate_party
                    '',  # candidate_color
                    '',  # candidate_gender
                    '',  # candidate_year_of_birth
                )),
                ','.join((
                    '',  # election_absolute_majority
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
                    '',  # candidate_family_name
                    '',  # candidate_first_name
                    '',  # candidate_id
                    '',  # candidate_elected
                    '',  # candidate_votes
                    '',  # candidate_party
                    '',  # candidate_color
                    'xxx',  # candidate_gender
                    '',  # candidate_year_of_birth
                )),
                ','.join((
                    '',  # election_absolute_majority
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
                    '',  # candidate_family_name
                    '',  # candidate_first_name
                    '',  # candidate_id
                    '',  # candidate_elected
                    '',  # candidate_votes
                    '',  # candidate_party
                    '',  # candidate_color
                    '',  # candidate_gender
                    'xxx',  # candidate_year_of_birth
                )),
                ','.join((
                    '',  # election_absolute_majority
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
                    '',  # candidate_family_name
                    '',  # candidate_first_name
                    '',  # candidate_id
                    '',  # candidate_elected
                    '',  # candidate_votes
                    '',  # candidate_party
                    'xxx',  # candidate_color
                    '',  # candidate_gender
                    '',  # candidate_year_of_birth
                )),
            ))
        ).encode('utf-8')), 'text/plain',
    )
    assert sorted((e.line, e.error.interpolate()) for e in errors) == [  # type: ignore[attr-defined]
        (2, 'Invalid integer: candidate_id'),
        (2, 'Invalid integer: candidate_votes'),
        (2, 'Invalid integer: election_absolute_majority'),
        (2, 'Invalid integer: entity_id'),
        (2, 'Invalid status'),
        (3, '1234 is unknown'),
        (3, 'Invalid gender: xxx'),
        (4, 'Invalid integer: candidate_year_of_birth'),
        (4, 'Invalid integer: entity_expats'),
        (5, 'Invalid color: candidate_party_color')
    ]


def test_import_internal_majorz_expats(session: Session) -> None:
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

    for has_expats in (False, True):
        election.has_expats = has_expats
        for entity_id in (9170, 0):
            raw_errors = import_election_internal_majorz(
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


def test_import_internal_majorz_temporary_results(session: Session) -> None:
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
    assert election.eligible_voters == 111
    assert election.expats == 0
    assert election.received_ballots == 11
    assert election.blank_ballots == 1
    assert election.invalid_ballots == 1
    assert election.accounted_votes == 52
    assert election.candidates[0].votes == 1


def test_import_internal_majorz_regional(session: Session) -> None:

    def create_csv(
        results: tuple[tuple[int, bool], ...]
    ) -> tuple[BytesIO, str]:
        lines = []
        lines.append((
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
        ))
        for entity_id, counted in results:
            lines.append((
                '',  # election_absolute_majority
                'unknown',  # election_status
                str(entity_id),  # entity_id
                str(counted),  # entity_counted
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
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((1701, False), (1702, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '1702 is not part of this business'
    ]

    # ZG, municipality, ok
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((1701, False),))
    )
    assert not errors
    assert election.progress == (0, 1)

    # ZG, none, ok
    election.domain = 'none'
    election.domain_segment = ''
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((1701, True), (1702, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # SG, district, too many districts
    principal = Canton(canton='sg')
    election.domain = 'district'
    election.domain_segment = 'Werdenberg'
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((3271, False), (3201, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '3201 is not part of Werdenberg'
    ]

    # SG, district, ok
    errors = import_election_internal_majorz(
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
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((3271, True), (3201, False)))
    )
    assert not errors
    assert election.progress == (1, 2)

    # GR, region, too many regions
    principal = Canton(canton='gr')
    election.domain = 'region'
    election.domain_segment = 'Ilanz'
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert [(e.error.interpolate()) for e in errors] == [  # type: ignore[attr-defined]
        '3513 is not part of Ilanz'
    ]

    # GR, region, ok
    errors = import_election_internal_majorz(
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
    errors = import_election_internal_majorz(
        election, principal,
        *create_csv(((3572, True), (3513, False)))
    )
    assert not errors
    assert election.progress == (1, 2)


def test_import_internal_majorz_optional_columns(session: Session) -> None:
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
                    'entity_expats',
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
                    'candidate_party_color',
                    'candidate_gender',
                    'candidate_year_of_birth',
                )),
                ','.join((
                    '',  # election_absolute_majority
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
                    'xxx',  # candidate_family_name
                    'xxx',  # candidate_first_name
                    '1',  # candidate_id
                    'false',  # candidate_elected
                    '1',  # candidate_votes
                    'FDP',  # candidate_party
                    '#123456',  # candidate_party_color
                    'female',  # candidate_gender,
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
    assert election.colors == {'FDP': '#123456'}
