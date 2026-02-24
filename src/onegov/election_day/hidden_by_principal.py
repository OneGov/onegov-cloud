from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Election
    from onegov.election_day.request import ElectionDayRequest


# Defaults for hiding elements if not value is provided in principal.yml
always_hide_candidate_by_entity_chart_percentages = False
always_hide_candidate_by_district_chart_percentages = False
hide_connections_chart_intermediate_results = False
hide_candidates_chart_intermediate_results = False


def hide_candidates_chart(
    election: Election,
    request: ElectionDayRequest,
    default: bool = hide_candidates_chart_intermediate_results
) -> bool:
    return request.app.principal.hidden_elements.get(
        'intermediate_results', {}).get(
        'candidates', {}).get(
        'chart', default) and not election.completed


def hide_connections_chart(
    election: Election,
    request: ElectionDayRequest,
    default: bool = hide_connections_chart_intermediate_results
) -> bool:
    return request.app.principal.hidden_elements.get(
        'intermediate_results', {}).get(
        'connections', {}).get(
        'chart', default) and not election.completed


def hide_candidate_entity_map_percentages(
    request: ElectionDayRequest,
    default: bool = always_hide_candidate_by_entity_chart_percentages
) -> bool:
    return request.app.principal.hidden_elements.get(
        'always', {}).get(
        'candidate-by-entity', {}).get(
        'chart_percentages', default)


def hide_candidate_district_map_percentages(
    request: ElectionDayRequest,
    default: bool = always_hide_candidate_by_district_chart_percentages
) -> bool:
    return request.app.principal.hidden_elements.get(
        'always', {}).get(
        'candidate-by-district', {}).get(
        'chart_percentages', default)
