from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_entity_filter
from onegov.election_day.utils import get_parameter
from onegov.election_day.utils.election import get_list_results
from onegov.election_day.utils.election import get_lists_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.json(
    model=Election,
    name='lists-data',
    permission=MaybePublic
)
def view_election_lists_data(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the lists as JSON. Used to for the lists bar chart. """

    limit = get_parameter(request, 'limit', int, None)
    names = get_parameter(request, 'names', list, None)
    sort_by_names = get_parameter(request, 'sort_by_names', bool, None)
    entity = request.params.get('entity', '')
    assert isinstance(entity, str)

    return get_lists_data(
        self,
        limit=limit,
        names=names,
        sort_by_names=sort_by_names or False,
        entities=[entity] if entity else None
    )


@ElectionDayApp.html(
    model=Election,
    name='lists-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_lists_chart(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the lists as bar chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    entity = request.params.get('entity', '')
    assert isinstance(entity, str)

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'lists-chart',
        'entity': entity
    }


@ElectionDayApp.html(
    model=Election,
    name='lists-table',
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
    lists = get_list_results(self, entities=[entity] if entity else None)

    return {
        'election': self,
        'lists': lists,
        'layout': ElectionLayout(self, request),
        'type': 'election-table',
        'scope': 'lists',
    }


@ElectionDayApp.html(
    model=Election,
    name='lists',
    template='election/lists.pt',
    permission=MaybePublic
)
def view_election_lists(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionLayout(self, request, 'lists')
    entity = request.params.get('entity', '')
    assert isinstance(entity, str)
    entities = get_entity_filter(request, self, 'lists', entity)
    lists = get_list_results(self, entities=[entity] if entity else None)

    return {
        'election': self,
        'layout': layout,
        'lists': lists,
        'entity': entity,
        'redirect_filters': {request.app.principal.label('entity'): entities}
    }


@ElectionDayApp.svg_file(
    model=Election,
    name='lists-svg',
    permission=MaybePublic
)
def view_election_lists_svg(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """ View the lists as SVG. """

    layout = ElectionLayout(self, request, 'lists')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
