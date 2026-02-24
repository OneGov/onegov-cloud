from __future__ import annotations

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.hidden_by_principal import hide_candidates_chart
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_entity_filter
from onegov.election_day.utils import get_parameter
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


election_incomplete_text = _(
    'The figure with elected candidates will be available '
    'as soon the final results are published.'
)


@ElectionDayApp.json(
    model=Election,
    name='candidates-data',
    permission=MaybePublic
)
def view_election_candidates_data(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the candidates as JSON.

    Used to for the candidates bar chart.

    """

    limit = get_parameter(request, 'limit', int, None)
    lists = get_parameter(request, 'lists', list, None)
    elected = get_parameter(request, 'elected', bool, None)
    sort_by_lists = get_parameter(request, 'sort_by_lists', bool, False)
    entity = request.params.get('entity', '')
    assert isinstance(entity, str)

    return get_candidates_data(
        self,
        limit=limit,
        lists=lists,
        elected=elected,
        sort_by_lists=sort_by_lists,
        entities=[entity] if entity else None
    )


@ElectionDayApp.html(
    model=Election,
    name='candidates-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_candidates_chart(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the candidates as bar chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    entity = request.params.get('entity', '')

    return {
        'skip_rendering': hide_candidates_chart(self, request),
        'help_text': election_incomplete_text,
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'candidates-chart',
        'entity': entity
    }


@ElectionDayApp.html(
    model=Election,
    name='candidates',
    template='election/candidates.pt',
    permission=MaybePublic
)
def view_election_candidates(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    entity = request.params.get('entity', '')
    assert isinstance(entity, str)
    entities = get_entity_filter(request, self, 'candidates', entity)
    candidates = get_candidates_results(
        self,
        request.session,
        entities=[entity] if entity else None
    ).all()
    any_elected = any(candidate.elected for candidate in candidates)

    return {
        'skip_rendering': hide_candidates_chart(self, request),
        'help_text': election_incomplete_text,
        'election': self,
        'layout': ElectionLayout(self, request, 'candidates'),
        'candidates': candidates,
        'any_elected': any_elected,
        'entity': entity,
        'redirect_filters': {request.app.principal.label('entity'): entities}
    }


@ElectionDayApp.html(
    model=Election,
    name='candidates-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_lists_table(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the lists as table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    entity = request.params.get('entity', '')
    assert isinstance(entity, str)
    candidates = get_candidates_results(
        self,
        request.session,
        entities=[entity] if entity else None
    ).all()

    return {
        'election': self,
        'candidates': candidates,
        'layout': ElectionLayout(self, request, 'candidates'),
        'type': 'election-table',
        'scope': 'candidates',
    }


@ElectionDayApp.svg_file(
    model=Election,
    name='candidates-svg',
    permission=MaybePublic
)
def view_election_candidates_svg(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """ View the candidates as SVG. """

    layout = ElectionLayout(self, request, 'candidates')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
