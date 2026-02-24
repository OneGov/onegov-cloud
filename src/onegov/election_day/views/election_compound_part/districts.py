from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_districts_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='districts',
    template='election_compound_part/districts.pt',
    permission=MaybePublic
)
def view_election_compound_part_districts(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:

    """" The districts view. """

    map_type = 'districts'
    if self.domain_elections == 'municipality':
        map_type = 'entities'

    return {
        'election_compound_part': self,
        'layout': ElectionCompoundPartLayout(self, request, 'districts'),
        'map_type': map_type,
        'data_url': request.link(self, name='by-district'),
        'embed_source': request.link(self, name='districts-map'),
    }


@ElectionDayApp.json(
    model=ElectionCompoundPart,
    name='by-district',
    permission=MaybePublic
)
def view_election_compound_part_by_district(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the districts/regions/municipalities as JSON for the map. """

    return get_districts_data(self, request.app.principal, request)


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='districts-map',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_list_by_district_chart(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:

    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    scope = 'districts'
    if self.domain_elections == 'municipality':
        scope = 'entities'

    return {
        'model': self,
        'layout': ElectionCompoundPartLayout(self, request, 'districts'),
        'type': 'map',
        'scope': scope,
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'b',
        'label_left_hand': '',
        'label_right_hand': '',
        'hide_percentages': True,
        'hide_legend': True,
        'data_url': request.link(self, name='by-district'),
    }


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='districts-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_part_districts_table(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:

    """" Displays the districts as standalone table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'election_compound': self,
        'layout': ElectionCompoundPartLayout(self, request, 'districts'),
        'type': 'election-compound-table',
        'scope': 'districts'
    }
