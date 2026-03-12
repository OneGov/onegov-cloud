from __future__ import annotations

from morepath import redirect
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_compound_summary
from onegov.election_day.utils.election_compound import (
    get_candidate_statistics)
from onegov.election_day.utils.election_compound import (
    get_elected_candidates)
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.security import MaybePublic


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=ElectionCompoundPart,
    request_method='HEAD',
    permission=MaybePublic
)
def view_election_compound_part_head(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> None:

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    permission=MaybePublic
)
def view_election_compound_part(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> Response:
    """" The main view. """

    return redirect(ElectionCompoundPartLayout(self, request).main_view)


@ElectionDayApp.json(
    model=ElectionCompoundPart,
    name='json',
    permission=MaybePublic
)
def view_election_compound_part_json(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> JSON_ro:
    """" The main view as JSON. """

    last_modified = self.last_modified
    assert last_modified is not None

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    session = request.app.session()
    embed = {'districts-map': request.link(self, 'districts-map')}
    charts: JSONObject = {}
    media: JSONObject = {'charts': charts}
    layout = ElectionCompoundPartLayout(self, request)
    layout.last_modified = last_modified
    for tab in ('party-strengths', ):
        layout = ElectionCompoundPartLayout(self, request, tab=tab)
        layout.last_modified = last_modified
        if layout.visible:
            embed[tab] = request.link(self, f'{tab}-chart')
        if layout.svg_path:
            charts[tab] = request.link(self, f'{tab}-svg')

    elected_candidates = get_elected_candidates(self, session).all()
    candidate_statistics = get_candidate_statistics(self, elected_candidates)
    districts: dict[str, JSONObject] = {
        election.id: {
            'name': election.domain_segment,
            'mandates': {
                'allocated': election.allocated_mandates or 0,
                'total': election.number_of_mandates or 0,
            },
            'progress': {
                'counted': election.progress[0] or 0,
                'total': election.progress[1] or 0
            },
        }
        for election in self.elections
    }

    _years, parties = get_party_results(self, json_serializable=True)

    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'last_modified': last_modified.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.progress[0] or 0,
            'total': self.progress[1] or 0
        },
        'districts': list(districts.values()),
        'elections': [
            request.link(election) for election in self.elections
        ],
        'elected_candidates': [
            {
                'first_name': candidate.first_name,
                'family_name': candidate.family_name,
                'party': candidate.party,
                'list': candidate.list,
                'district': districts[candidate.election_id]['name']
            }
            for candidate in elected_candidates
            if candidate.election_id is not None
        ],
        'candidate_statistics': candidate_statistics,  # type:ignore[dict-item]
        'parties': parties,
        'title': self.title_translations,
        'type': 'election_compound_part',
        'url': request.link(self),
        'embed': embed,
        'media': media,
    }


@ElectionDayApp.json(
    model=ElectionCompoundPart,
    name='summary',
    permission=MaybePublic
)
def view_election_compound_part_summary(
    self: ElectionCompoundPart,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the summary of the election compound part as JSON. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_election_compound_summary(
        self, request, type_='election_compound_part'
    )
