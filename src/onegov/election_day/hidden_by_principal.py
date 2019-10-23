
# Defaults for hiding elements if not value is provided in principal.yml
always_hide_candidate_by_entity_chart_percentages = False
hide_connections_chart_intermediate_results = False
hide_candidates_chart_intermediate_results = True


def hide_candidates_chart(
        election,
        request,
        default=hide_candidates_chart_intermediate_results):
    return request.app.principal.hidden_elements.get(
        'intermediate_results', {}).get(
        'candidates', {}).get(
        'chart', default) and not election.completed


def hide_connections_chart(
        election,
        request,
        default=hide_connections_chart_intermediate_results):
    return request.app.principal.hidden_elements.get(
        'intermediate_results', {}).get(
        'connections', {}).get(
        'chart', default) and not election.completed


def hide_candidate_map_percentages(
        request,
        default=always_hide_candidate_by_entity_chart_percentages):
    return request.app.principal.hidden_elements.get(
        'always', {}).get(
        'candidate-by-entity', {}).get(
        'chart_percentages', default)
