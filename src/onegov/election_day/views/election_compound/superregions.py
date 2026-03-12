from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_superregions
from onegov.election_day.utils.election_compound import get_superregions_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions',
    template='election_compound/superregions.pt',
    permission=MaybePublic
)
def view_election_compound_superregions(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" The superregions view. """

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'superregions': get_superregions(self, request.app.principal),
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='by-superregion',
    permission=MaybePublic
)
def view_election_compound_by_superregion(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the superregions/regions/municipalities as JSON for the map. """

    return get_superregions_data(self, request.app.principal, request)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions-map',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_list_by_superregion_chart(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'type': 'map',
        'scope': 'districts',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'b',
        'label_left_hand': '',
        'label_right_hand': '',
        'hide_percentages': True,
        'hide_legend': True,
        'data_url': request.link(self, name='by-superregion'),
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_superregions_table(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" Displays the superregions as standalone table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'type': 'election-compound-table',
        'scope': 'superregions',
        'superregions': get_superregions(self, request.app.principal),
    }
