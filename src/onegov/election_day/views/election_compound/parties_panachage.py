from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.parties import get_parties_panachage_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.json(
    model=ElectionCompound,
    name='parties-panachage-data',
    permission=MaybePublic
)
def view_election_compound_parties_panachage_data(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    return get_parties_panachage_data(self, request)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties-panachage-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_parties_panachage_chart(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" View the panachage data as sankey chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request),
        'type': 'parties-panachage-chart',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties-panachage',
    template='election_compound/parties_panachage.pt',
    permission=MaybePublic
)
def view_election_compound_parties_panachage(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'parties-panachage')

    return {
        'election_compound': self,
        'layout': layout
    }


@ElectionDayApp.svg_file(
    model=ElectionCompound,
    name='parties-panachage-svg',
    permission=MaybePublic
)
def view_election_compound_parties_panachage_svg(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """ View the panachage as SVG. """

    layout = ElectionCompoundLayout(self, request, 'parties-panachage')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
