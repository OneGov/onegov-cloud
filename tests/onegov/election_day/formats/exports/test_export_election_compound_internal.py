from __future__ import annotations

from collections import OrderedDict
from datetime import date
from onegov.election_day.formats import export_election_compound_internal
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
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


def majorz_election() -> Election:
    # election
    election = Election(
        title='Majorz',
        short_title='M',
        id='majorz',
        shortcode='2',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]
    election.short_title_translations['it_CH'] = 'X'  # type: ignore[index]

    # candidates
    candidate_id_1 = uuid4()
    candidate_id_2 = uuid4()
    election.candidates.append(
        Candidate(
            id=candidate_id_1,
            elected=True,
            candidate_id='1',
            family_name='Quimby',
            first_name='Joe',
            party='Republican Party',
            gender='male',
            year_of_birth=1970
        )
    )
    election.candidates.append(
        Candidate(
            id=candidate_id_2,
            elected=False,
            candidate_id='2',
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            party='Democratic Party',
        )
    )

    # results
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
        CandidateResult(candidate_id=candidate_id_1, votes=520)
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_2, votes=111)
    )
    election.results.append(election_result)
    return election


def proporz_election() -> ProporzElection:
    # election
    election = ProporzElection(
        title='Proporz',
        short_title='P',
        id='proporz',
        shortcode='1',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144,
        status=None,
        domain_supersegment=''
    )
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]
    election.short_title_translations['it_CH'] = 'Y'  # type: ignore[index]

    # lists
    list_id_1 = uuid4()
    list_id_2 = uuid4()
    connection = ListConnection(connection_id='A')
    subconnection = ListConnection(id=uuid4(), connection_id='A.1')
    connection.children.append(subconnection)
    election.list_connections.append(connection)
    list_1 = List(
        id=list_id_1,
        list_id='1',
        number_of_mandates=1,
        name='Quimby Again!',
    )
    list_2 = List(
        id=list_id_2,
        list_id='2',
        number_of_mandates=0,
        name='Kwik-E-Major',
        connection_id=subconnection.id
    )
    election.lists.append(list_1)
    election.lists.append(list_2)

    # candidates
    candidate_id_1 = uuid4()
    candidate_id_2 = uuid4()
    election.candidates.append(
        Candidate(
            id=candidate_id_1,
            elected=True,
            candidate_id='1',
            list_id=list_id_1,
            family_name='Quimby',
            first_name='Joe',
            party='Republican Party',
            gender='male',
            year_of_birth=1970
        )
    )
    election.candidates.append(
        Candidate(
            id=candidate_id_2,
            elected=False,
            candidate_id='2',
            list_id=list_id_2,
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            party='Democratic Party',
        )
    )

    # results
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
        invalid_votes=120,
    )

    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_1, votes=520)
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_2, votes=111)
    )

    election_result.list_results.append(
        ListResult(list_id=list_id_1, votes=520)
    )
    election_result.list_results.append(
        ListResult(list_id=list_id_2, votes=111)
    )
    election.results.append(election_result)

    list_1.panachage_results.append(
        ListPanachageResult(source_id=list_2.id, votes=12)
    )
    list_1.panachage_results.append(
        ListPanachageResult(source_id=None, votes=4)
    )

    return election


def test_election_compound_export(session: Session) -> None:
    session.add(
        ElectionCompound(
            title='Elections',
            short_title='E',
            domain='canton',
            date=date(2015, 6, 14),
        )
    )
    election = majorz_election()
    election.colors = {'Democratic Party': '#112233'}
    session.add(election)
    election = proporz_election()
    election.colors = {
        'Democratic Party': '#112233',
        'Kwik-E-Major': '#223344'
    }
    session.add(election)
    session.flush()
    election_compound = session.query(ElectionCompound).one()
    election_compound.title_translations['it_CH'] = 'Elezioni'  # type: ignore[index]
    election_compound.short_title_translations['it_CH'] = 'E'  # type: ignore[index]

    assert export_election_compound_internal(
        election_compound, ['de_CH']
    ) == []

    election_compound.elections = session.query(Election).filter_by(
        id='majorz'
    ).all()
    session.flush()
    export = export_election_compound_internal(
        election_compound, ['de_CH', 'fr_CH', 'it_CH']
    )
    assert export[0] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_id': 'majorz',
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'M',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'X',
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
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111
    })
    assert export[1] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_id': 'majorz',
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'M',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'X',
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
        'candidate_party_color': '',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520
    })

    election_compound.elections = session.query(Election).all()
    session.flush()
    export = export_election_compound_internal(
        election_compound, ['de_CH', 'fr_CH', 'it_CH']
    )

    assert export[0] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_id': 'proporz',
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'P',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'Y',
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
        'list_color': '#223344',
        'list_number_of_mandates': 0,
        'list_votes': 111,
        'list_connection': 'A.1',
        'list_connection_parent': 'A',
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111,
        'list_panachage_votes_from_list_1': None,
        'list_panachage_votes_from_list_2': None,
        'list_panachage_votes_from_list_999': None
    })

    assert export[1] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_id': 'proporz',
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'P',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'Y',
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
        'list_panachage_votes_from_list_999': 4
    })

    assert export[2] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_id': 'majorz',
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'M',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'X',
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
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111
    })

    assert export[3] == OrderedDict({
        'compound_id': 'e',
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_short_title_de_CH': 'E',
        'compound_short_title_fr_CH': '',
        'compound_short_title_it_CH': 'E',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_id': 'majorz',
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_short_title_de_CH': 'M',
        'election_short_title_fr_CH': '',
        'election_short_title_it_CH': 'X',
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
        'candidate_party_color': '',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520
    })
