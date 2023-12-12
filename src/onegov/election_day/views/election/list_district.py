from onegov.ballot import Election
from onegov.ballot import List
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import func


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import ProporzElection
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def list_options(
    request: 'ElectionDayRequest',
    election: Election
) -> list[tuple[str, str]]:

    if election.type != 'proporz':
        return []

    election = cast('ProporzElection', election)

    mandates = request.translate(request.app.principal.label('mandates'))
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
        for list_ in election.lists.order_by(None).order_by(
            List.number_of_mandates.desc(),
            func.lower(List.name)
        )
    ]


@ElectionDayApp.json(
    model=List,
    name='by-district',
    permission=Public
)
def view_list_by_district(
    self: List,
    request: 'ElectionDayRequest'
) -> 'JSON_ro':
    """" View the list by district as JSON. """

    return self.percentage_by_district  # type:ignore[return-value]


@ElectionDayApp.html(
    model=Election,
    name='list-by-district',
    template='election/heatmap.pt',
    permission=Public
)
def view_election_list_by_district(
    self: Election,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """" View the list as heatmap by district. """

    layout = ElectionLayout(self, request, 'list-by-district')

    options = list_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'districts',
        'data_url': data_url,
        'embed_source': request.link(
            self,
            name='list-by-district-chart',
            # FIXME: Should we assert that the locale is set?
            query_params={'locale': request.locale}  # type:ignore[dict-item]
        )
    }


@ElectionDayApp.html(
    model=Election,
    name='list-by-district-chart',
    template='embed.pt',
    permission=Public
)
def view_election_list_by_district_chart(
    self: Election,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response: 'Response') -> None:
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
