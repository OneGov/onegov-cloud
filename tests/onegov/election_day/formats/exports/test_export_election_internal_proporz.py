from __future__ import annotations

from collections import OrderedDict
from datetime import date
from onegov.election_day.formats import export_election_internal_proporz
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from onegov.election_day.models import ProporzElection
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_export_election_internal_proporz(session: Session) -> None:
    election = ProporzElection(
        title='Wahl',
        short_title='W',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]
    election.short_title_translations['it_CH'] = 'E'  # type: ignore[index]
    election.colors = {
        'Kwik-E-Major': '#112233',
        'Democratic Party': '#223344'
    }

    connection = ListConnection(
        id=uuid4(),
        connection_id='A'
    )
    subconnection = ListConnection(
        id=uuid4(),
        connection_id='A.1'
    )
    connection.children.append(subconnection)
    election.list_connections.append(connection)

    list_1 = List(
        id=uuid4(),
        list_id='1',
        number_of_mandates=1,
        name='Quimby Again!',
    )
    list_2 = List(
        id=uuid4(),
        list_id='2',
        number_of_mandates=0,
        name='Kwik-E-Major',
        connection_id=subconnection.id
    )
    election.lists.append(list_1)
    election.lists.append(list_2)

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
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
        list_id=list_2.id,
        family_name='Nahasapeemapetilon',
        first_name='Apu',
        party='Democratic Party',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    session.add(election)
    session.flush()

    assert export_election_internal_proporz(election, ['de_CH']) == []

    election_result = ElectionResult(
        id=uuid4(),
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
    election.results.append(election_result)

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
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result.id,
            source_id=list_2.id,
            votes=11
        )
    )
    candidate_1.panachage_results.append(
        CandidatePanachageResult(
            election_result_id=election_result.id,
            source_id=None,
            votes=3
        )
    )

    election_result.list_results.append(
        ListResult(
            list_id=list_1.id,
            votes=520
        )
    )
    election_result.list_results.append(
        ListResult(
            list_id=list_2.id,
            votes=111
        )
    )

    list_1.panachage_results.append(
        ListPanachageResult(
            source_id=list_2.id,
            votes=12
        )
    )
    list_1.panachage_results.append(
        ListPanachageResult(
            source_id=None,
            votes=4
        )
    )

    session.flush()

    assert export_election_internal_proporz(
        election, ['de_CH', 'fr_CH', 'it_CH']
    ) == [
        OrderedDict({
            'election_id': 'w',
            'election_title_de_CH': 'Wahl',
            'election_title_fr_CH': '',
            'election_title_it_CH': 'Elezione',
            'election_short_title_de_CH': 'W',
            'election_short_title_fr_CH': '',
            'election_short_title_it_CH': 'E',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
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
            'list_name': 'Kwik-E-Major',
            'list_id': '2',
            'list_color': '#112233',
            'list_number_of_mandates': 0,
            'list_votes': 111,
            'list_connection': 'A.1',
            'list_connection_parent': 'A',
            'candidate_family_name': 'Nahasapeemapetilon',
            'candidate_first_name': 'Apu',
            'candidate_id': '2',
            'candidate_elected': False,
            'candidate_party': 'Democratic Party',
            'candidate_party_color': '#223344',
            'candidate_gender': '',
            'candidate_year_of_birth': '',
            'candidate_votes': 111,
            'list_panachage_votes_from_list_1': None,
            'list_panachage_votes_from_list_2': None,
            'list_panachage_votes_from_list_999': None,
            'candidate_panachage_votes_from_list_1': None,
            'candidate_panachage_votes_from_list_2': None,
            'candidate_panachage_votes_from_list_999': None,
        }),
        OrderedDict({
            'election_id': 'w',
            'election_title_de_CH': 'Wahl',
            'election_title_fr_CH': '',
            'election_title_it_CH': 'Elezione',
            'election_short_title_de_CH': 'W',
            'election_short_title_fr_CH': '',
            'election_short_title_it_CH': 'E',
            'election_date': '2015-06-14',
            'election_domain': 'federation',
            'election_type': 'proporz',
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
            'list_name': 'Quimby Again!',
            'list_id': '1',
            'list_color': '',
            'list_number_of_mandates': 1,
            'list_votes': 520,
            'list_connection': None,
            'list_connection_parent': None,
            'candidate_family_name': 'Quimby',
            'candidate_first_name': 'Joe',
            'candidate_id': '1',
            'candidate_elected': True,
            'candidate_party': 'Republican Party',
            'candidate_party_color': '',
            'candidate_gender': 'male',
            'candidate_year_of_birth': 1970,
            'candidate_votes': 520,
            'list_panachage_votes_from_list_1': None,
            'list_panachage_votes_from_list_2': 12,
            'list_panachage_votes_from_list_999': 4,
            'candidate_panachage_votes_from_list_1': None,
            'candidate_panachage_votes_from_list_2': 11,
            'candidate_panachage_votes_from_list_999': 3,
        })
    ]
