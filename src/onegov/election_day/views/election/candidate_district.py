from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.hidden_by_principal import (
    hide_candidate_district_map_percentages)
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def candidate_options(
    request: 'ElectionDayRequest',
    election: Election
) -> list[tuple[str, str]]:

    elected = request.translate(_("Elected")).lower()
    completed = election.completed
    return [
        (
            request.link(candidate_, name='by-district'),
            '{} {}'.format(
                f'{candidate_.family_name} {candidate_.first_name}',
                (f'({elected})' if completed
                 and candidate_.elected else '')
            ).strip()
        )
        # todo:
        for candidate_ in election.candidates.order_by(None).order_by(
            Candidate.elected.desc(),
            func.lower(Candidate.family_name),
            func.lower(Candidate.first_name),
        )
    ]


@ElectionDayApp.json(
    model=Candidate,
    name='by-district',
    permission=Public
)
def view_candidate_by_district(
    self: Candidate,
    request: 'ElectionDayRequest'
) -> 'JSON_ro':
    """" View the candidate by district as JSON. """

    return self.percentage_by_district  # type:ignore[return-value]


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-district',
    template='election/heatmap.pt',
    permission=Public
)
def view_election_candidate_by_district(
    self: Election,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """" View the candidate as heatmap by district. """

    layout = ElectionLayout(self, request, 'candidate-by-district')

    options = candidate_options(request, self)
    data_url = options[0][0] if options else None
    by = request.translate(layout.label('district'))
    by = by.lower() if request.locale != 'de_CH' else by

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'districts',
        'data_url': data_url,
        'embed_source': request.link(
            self,
            name='candidate-by-district-chart',
            # FIXME: Should we assert that locale is set?
            query_params={'locale': request.locale}  # type:ignore[dict-item]
        ),
        'hide_percentages': hide_candidate_district_map_percentages(request),
        'figcaption': _(
            'The map shows the percentage of votes for the selected candidate '
            'by ${by}.',
            mapping={'by': by}
        )
    }


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-district-chart',
    template='embed.pt',
    permission=Public
)
def view_election_candidate_by_district_chart(
    self: Election,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response: 'Response') -> None:
        add_last_modified_header(response, self.last_modified)

    options = candidate_options(request, self)
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
        'options': options,
        'hide_percentages': hide_candidate_district_map_percentages(request)
    }
