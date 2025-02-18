from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_list_groups_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.json(
    model=ElectionCompound,
    name='list-groups-data',
    permission=MaybePublic
)
def view_election_compound_list_groups_data(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the list groups as JSON. Used to for the lists bar chart. """

    return get_list_groups_data(self)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_list_groups_chart(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" View the list groups as bar chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request),
        'type': 'list-groups-chart',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_list_groups_table(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" View the list groups as table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'groups': get_list_groups(self),
        'layout': ElectionCompoundLayout(self, request),
        'type': 'election-compound-table',
        'scope': 'list-groups',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups',
    template='election_compound/list_groups.pt',
    permission=MaybePublic
)
def view_election_compound_list_groups(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'list-groups')

    return {
        'election_compound': self,
        'layout': layout,
        'groups': get_list_groups(self),
    }


@ElectionDayApp.svg_file(
    model=ElectionCompound,
    name='list-groups-svg',
    permission=MaybePublic
)
def view_election_compound_list_groups_svg(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """ View the list groups as SVG. """

    layout = ElectionCompoundLayout(self, request, 'list-groups')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
