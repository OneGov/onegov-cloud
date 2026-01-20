from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_parameter
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_data
from onegov.election_day.utils.parties import get_party_results_deltas


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.json(
    model=ElectionCompoundPart,
    name='party-strengths-data',
    permission=MaybePublic
)
def view_election_compound_part_party_strengths_data(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> JSON_ro:
    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    horizontal = get_parameter(request, 'horizontal', bool, False)
    return get_party_results_data(self, horizontal)


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='party-strengths-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_part_party_strengths_chart(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:
    """" View the party strengths as grouped bar chart. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundPartLayout(self, request),
        'type': 'party-strengths-chart',
        'horizontal': self.horizontal_party_strengths
    }


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='party-strengths-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_compound_party_strengths_table(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:
    """" View the party strengths as table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    party_years, parties = get_party_results(self)
    party_deltas, party_results = get_party_results_deltas(
        self, party_years, parties
    )
    year = request.params.get('year', '')

    return {
        'layout': ElectionCompoundPartLayout(self, request, 'party-strengths'),
        'type': 'election-compound-part-table',
        'scope': 'party-strengths',
        'party_results': party_results,
        'party_years': party_years,
        'year': year,
        'party_deltas': party_deltas
    }


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='party-strengths',
    template='election_compound_part/party_strengths.pt',
    permission=MaybePublic
)
def view_election_compound_part_party_strengths(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionCompoundPartLayout(self, request, 'party-strengths')

    party_years, parties = get_party_results(self)
    party_deltas, party_results = get_party_results_deltas(
        self, party_years, parties
    )

    return {
        'election_compound_part': self,
        'layout': layout,
        'party_results': party_results,
        'party_years': party_years,
        'party_deltas': party_deltas
    }


@ElectionDayApp.svg_file(
    model=ElectionCompoundPart,
    name='party-strengths-svg',
    permission=MaybePublic
)
def view_election_compound_part_party_strengths_svg(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> RenderData:
    """ View the party strengths as SVG. """

    layout = ElectionCompoundPartLayout(self, request, 'party-strengths')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
