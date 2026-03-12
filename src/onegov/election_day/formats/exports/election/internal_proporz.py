from __future__ import annotations

from collections import OrderedDict
from itertools import groupby
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from operator import itemgetter
from sqlalchemy.orm import aliased
from sqlalchemy.orm import object_session


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID


def export_election_internal_proporz(
    election: Election,
    locales: Collection[str]
) -> list[dict[str, Any]]:
    """ Returns all data connected to this election as list with dicts.

    This is meant as a base for json/csv/excel exports. The result is
    therefore a flat list of dictionaries with repeating values to avoid
    the nesting of values. Each record in the resulting list is a single
    candidate result for each political entity. Party results are not
    included in the export (since they are not really connected with the
    lists).

    """

    session = object_session(election)
    assert session is not None

    ids = session.query(ElectionResult.id)
    ids = ids.filter(ElectionResult.election_id == election.id)

    SubListConnection = aliased(ListConnection)  # noqa: N806
    results = session.query(
        CandidateResult.votes,
        ElectionResult.superregion,
        ElectionResult.district,
        ElectionResult.name.label('entity_name'),
        ElectionResult.entity_id,
        ElectionResult.counted,
        ElectionResult.eligible_voters,
        ElectionResult.expats,
        ElectionResult.received_ballots,
        ElectionResult.blank_ballots,
        ElectionResult.invalid_ballots,
        ElectionResult.unaccounted_ballots,
        ElectionResult.accounted_ballots,
        ElectionResult.blank_votes,
        ElectionResult.invalid_votes,
        ElectionResult.accounted_votes,
        List.name.label('list_name'),
        List.list_id,
        List.number_of_mandates.label('list_number_of_mandates'),
        SubListConnection.connection_id,
        ListConnection.connection_id.label('parent_connection_id'),
        Candidate.family_name,
        Candidate.first_name,
        Candidate.candidate_id,
        Candidate.elected,
        Candidate.party,
        Candidate.gender,
        Candidate.year_of_birth,
    )
    results = results.outerjoin(CandidateResult.candidate)
    results = results.outerjoin(CandidateResult.election_result)
    results = results.outerjoin(Candidate.list)
    results = results.outerjoin(SubListConnection, List.connection)
    results = results.outerjoin(SubListConnection.parent)
    results = results.outerjoin(Candidate.election)
    results = results.filter(CandidateResult.election_result_id.in_(ids))
    results = results.order_by(
        ElectionResult.district,
        ElectionResult.name,
        List.name,
        Candidate.family_name,
        Candidate.first_name
    )

    # We need to merge in the list results per entity
    list_results = session.query(
        ListResult.votes,
        ElectionResult.entity_id,
        List.list_id
    )
    list_results = list_results.outerjoin(ListResult.election_result)
    list_results = list_results.outerjoin(ListResult.list)
    list_results = list_results.filter(
        ListResult.election_result_id.in_(ids)
    )
    list_results = list_results.order_by(
        ElectionResult.entity_id,
        List.list_id
    )
    list_results_grouped = {}
    for key, group in groupby(list_results, itemgetter(1)):
        list_results_grouped[key] = {g[2]: g[0] for g in group}

    # We need to collect the panachage results per list
    list_ids_q = session.query(List.id, List.list_id)
    list_ids_q = list_ids_q.filter(List.election_id == election.id)
    list_ids: dict[UUID | None, str] = dict(list_ids_q.tuples())
    list_ids[None] = '999'
    list_panachage_results = session.query(ListPanachageResult)
    list_panachage_results = list_panachage_results.filter(
        ListPanachageResult.target_id.in_(list_ids)
    )
    list_panachage: dict[str, dict[str, int]] = {}
    for list_result in list_panachage_results:
        target = list_ids[list_result.target_id]
        source = list_ids[list_result.source_id]
        list_panachage.setdefault(target, {})
        list_panachage[target][source] = list_result.votes

    # We need to collect the panchage results per candidate
    candidate_ids_q = session.query(Candidate.id, Candidate.candidate_id)
    candidate_ids_q = candidate_ids_q.filter(
        Candidate.election_id == election.id
    )
    candidate_ids = dict(candidate_ids_q.tuples())
    candidate_panachage_results = session.query(
        CandidatePanachageResult.target_id,
        CandidatePanachageResult.source_id,
        CandidatePanachageResult.votes,
        ElectionResult.entity_id
    )
    candidate_panachage_results = candidate_panachage_results.outerjoin(
        ElectionResult
    )
    candidate_panachage_results = candidate_panachage_results.filter(
        CandidatePanachageResult.target_id.in_(candidate_ids)
    )
    candidate_panachage: dict[str, dict[str, dict[str, int]]] = {}
    for candidate_result in candidate_panachage_results:
        target = candidate_ids[candidate_result.target_id]
        source = list_ids[candidate_result.source_id]
        entity = candidate_result.entity_id
        candidate_panachage.setdefault(entity, {})
        candidate_panachage[entity].setdefault(target, {})
        candidate_panachage[entity][target][source] = candidate_result.votes

    titles = election.title_translations or {}
    short_titles = election.short_title_translations or {}

    rows: list[dict[str, Any]] = []
    for result in results:
        row: dict[str, Any] = OrderedDict()
        row['election_id'] = election.id
        for locale in locales:
            title = titles.get(locale, '') or ''
            row[f'election_title_{locale}'] = title.strip()
        for locale in locales:
            title = short_titles.get(locale, '') or ''
            row[f'election_short_title_{locale}'] = title.strip()
        row['election_date'] = election.date.isoformat()
        row['election_domain'] = election.domain
        row['election_type'] = election.type
        row['election_mandates'] = election.number_of_mandates
        row['election_absolute_majority'] = election.absolute_majority
        row['election_status'] = election.status or 'unknown'
        row['entity_superregion'] = result.superregion or ''
        row['entity_district'] = result.district or ''
        row['entity_name'] = result.entity_name
        row['entity_id'] = result.entity_id
        row['entity_counted'] = result.counted
        row['entity_eligible_voters'] = result.eligible_voters
        row['entity_expats'] = result.expats
        row['entity_received_ballots'] = result.received_ballots
        row['entity_blank_ballots'] = result.blank_ballots
        row['entity_invalid_ballots'] = result.invalid_ballots
        row['entity_unaccounted_ballots'] = result.unaccounted_ballots
        row['entity_accounted_ballots'] = result.accounted_ballots
        row['entity_blank_votes'] = result.blank_votes
        row['entity_invalid_votes'] = result.invalid_votes
        row['entity_accounted_votes'] = result.accounted_votes
        row['list_name'] = result.list_name
        row['list_id'] = result.list_id
        row['list_color'] = election.colors.get(result.list_name, '')
        row['list_number_of_mandates'] = result.list_number_of_mandates
        row['list_votes'] = list_results_grouped.get(
            result.entity_id, {}
        ).get(result.list_id, 0)
        row['list_connection'] = result.connection_id
        row['list_connection_parent'] = result.parent_connection_id
        row['candidate_family_name'] = result.family_name
        row['candidate_first_name'] = result.first_name
        row['candidate_id'] = result.candidate_id
        row['candidate_elected'] = result.elected
        row['candidate_party'] = result.party
        row['candidate_party_color'] = election.colors.get(result.party, '')
        row['candidate_gender'] = result.gender or ''
        row['candidate_year_of_birth'] = result.year_of_birth or ''
        row['candidate_votes'] = result.votes
        if list_panachage:
            for id_ in sorted(list_ids.values()):
                key = f'list_panachage_votes_from_list_{id_}'
                row[key] = list_panachage.get(result.list_id, {}).get(id_)
        if candidate_panachage:
            for id_ in sorted(list_ids.values()):
                key = f'candidate_panachage_votes_from_list_{id_}'
                row[key] = candidate_panachage.get(
                    result.entity_id, {}
                ).get(result.candidate_id, {}).get(id_)
        rows.append(row)

    return rows
