from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.hidden_by_principal import (
    hide_connections_chart)
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_connection_results_api
from onegov.election_day.utils.election import get_connections_data
from onegov.election_day import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


election_incomplete_text = _(
    'The figure with the list connections will be available '
    'as soon the final results are published.'
)


@ElectionDayApp.json(
    model=Election,
    name='connections-data',
    permission=MaybePublic
)
def view_election_connections_data(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the list connections as JSON.

    Used to for the connection sankey chart.

    """
    return get_connections_data(self)


@ElectionDayApp.html(
    model=Election,
    name='connections-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_connections_chart(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the connections as sankey chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    skip_rendering = hide_connections_chart(self, request)

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'connections-chart',
        'skip_rendering': skip_rendering,
        'help_text': election_incomplete_text
    }


@ElectionDayApp.html(
    model=Election,
    name='connections-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_connections_table(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the connections tables as widget. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'connections': get_connection_results_api(self, request.session),
        'type': 'election-table',
        'scope': 'connections'
    }


@ElectionDayApp.html(
    model=Election,
    name='connections',
    template='election/connections.pt',
    permission=MaybePublic
)
def view_election_connections(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionLayout(self, request, 'connections')
    return {
        'election': self,
        'layout': layout,
        'connections': get_connection_results_api(self, request.session),
        'skip_rendering': hide_connections_chart(self, request),
        'help_text': election_incomplete_text,
    }


@ElectionDayApp.svg_file(
    model=Election,
    name='connections-svg',
    permission=MaybePublic
)
def view_election_connections_svg(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """ View the connections as SVG. """

    layout = ElectionLayout(self, request, 'connections')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
