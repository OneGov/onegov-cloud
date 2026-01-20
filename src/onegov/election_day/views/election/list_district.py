from __future__ import annotations

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.models import List
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def list_options(
    request: ElectionDayRequest,
    election: Election
) -> list[tuple[str, str]]:

    if election.type != 'proporz':
        return []

    election = cast('ProporzElection', election)
    mandates = request.translate(request.app.principal.label('mandates'))

    def ordering(list_: List) -> tuple[int, str]:
        return (-list_.number_of_mandates, list_.name.lower())

    return [
        (
            request.link(list_, name='by-district'),
            '{} {}'.format(
                list_.name,
                (
                    f'({list_.number_of_mandates} {mandates})'
                    if list_.number_of_mandates and election.completed else ''
                )
            ).strip()
        )
        for list_ in sorted(election.lists, key=ordering)
    ]


@ElectionDayApp.json(
    model=List,
    name='by-district',
    permission=MaybePublic
)
def view_list_by_district(
    self: List,
    request: ElectionDayRequest
) -> JSON_ro:
    """" View the list by district as JSON. """

    return self.percentage_by_district  # type:ignore[return-value]


@ElectionDayApp.html(
    model=Election,
    name='list-by-district',
    template='election/heatmap.pt',
    permission=MaybePublic
)
def view_election_list_by_district(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View the list as heatmap by district. """

    layout = ElectionLayout(self, request, 'list-by-district')

    options = list_options(request, self)
    data_url = options[0][0] if options else None
    by = request.translate(layout.label('district'))
    by = by.lower() if request.locale != 'de_CH' else by

    assert request.locale

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'districts',
        'data_url': data_url,
        'embed_source': request.link(
            self,
            name='list-by-district-chart',
            query_params={'locale': request.locale}
        ),
        'figcaption': _(
            'The map shows the percentage of votes for the selected list '
            'by ${by}.',
            mapping={'by': by}
        )
    }


@ElectionDayApp.html(
    model=Election,
    name='list-by-district-chart',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_list_by_district_chart(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    options = list_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'map',
        'scope': 'districts',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'r',
        'label_left_hand': '0%',
        'label_right_hand': '100%',
        'data_url': data_url,
        'options': options
    }
