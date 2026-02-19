from __future__ import annotations

from collections import OrderedDict
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionResult
from sqlalchemy.orm import object_session


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection


def export_election_internal_majorz(
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

    results = session.query(
        CandidateResult.votes,
        ElectionResult.superregion,
        ElectionResult.district,
        ElectionResult.name,
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
    results = results.outerjoin(Candidate.election)
    results = results.filter(CandidateResult.election_result_id.in_(ids))
    results = results.order_by(
        ElectionResult.district,
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name
    )

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
        row['entity_name'] = result.name
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
        row['candidate_family_name'] = result.family_name
        row['candidate_first_name'] = result.first_name
        row['candidate_id'] = result.candidate_id
        row['candidate_elected'] = result.elected
        row['candidate_party'] = result.party
        row['candidate_party_color'] = election.colors.get(result.party, '')
        row['candidate_gender'] = result.gender or ''
        row['candidate_year_of_birth'] = result.year_of_birth or ''
        row['candidate_votes'] = result.votes
        rows.append(row)

    return rows
