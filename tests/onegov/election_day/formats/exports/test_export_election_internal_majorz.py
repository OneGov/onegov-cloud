from __future__ import annotations

from datetime import date
from onegov.election_day.formats import export_election_internal_majorz
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionResult
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_export_election_internal_majorz(session: Session) -> None:
    election = Election(
        title='Wahl',
        short_title='W',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]
    election.short_title_translations['it_CH'] = 'E'  # type: ignore[index]
    election.colors = {'Republican Party': '#112233'}

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        family_name='Quimby',
        first_name='Joe',
        party='Republican Party',
        gender='male',
        year_of_birth=1970
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        family_name='Nahasapeemapetilon',
        first_name='Apu',
        party='Democratic Party',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    session.add(election)
    session.flush()

    assert export_election_internal_majorz(election, ['de_CH']) == []

    election_result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        expats=35,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )

    election_result.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=520,
        )
    )
    election_result.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=111
        )
    )
    election.results.append(election_result)

    session.flush()

    export = export_election_internal_majorz(
        election, ['de_CH', 'fr_CH', 'it_CH']
    )

    assert export[0] == {
        'election_id': 'w',
        'election_title_de_CH': 'Wahl',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'W',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'E',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_party_color': '',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111,
    }
    assert export[1] == {
        'election_id': 'w',
        'election_title_de_CH': 'Wahl',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'W',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'E',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Quimby',
        'candidate_first_name': 'Joe',
        'candidate_id': '1',
        'candidate_elected': True,
        'candidate_party': 'Republican Party',
        'candidate_party_color': '#112233',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520,
    }
