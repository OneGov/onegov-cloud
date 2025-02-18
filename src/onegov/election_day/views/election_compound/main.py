from __future__ import annotations

from collections import defaultdict
from morepath import redirect
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_compound_summary
from onegov.election_day.utils.election_compound import (
    get_candidate_statistics)
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_superregions
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.security import MaybePublic


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=ElectionCompound,
    request_method='HEAD',
    permission=MaybePublic
)
def view_election_compound_head(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> None:

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.html(
    model=ElectionCompound,
    permission=MaybePublic
)
def view_election_compound(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> Response:
    """" The main view. """

    return redirect(ElectionCompoundLayout(self, request).main_view)


@ElectionDayApp.json(
    model=ElectionCompound,
    name='json',
    permission=MaybePublic
)
def view_election_compound_json(
    self: ElectionCompound,
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
    embed = defaultdict(list)
    charts: JSONObject = {}
    media: JSONObject = {'charts': charts}
    layout = ElectionCompoundLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    embed['districts-map'].append(request.link(self, 'districts-map'))
    if layout.has_superregions:
        embed['superregions-map'].append(
            request.link(self, 'superregions-map')
        )
    for tab in (
        'seat-allocation',
        'list-groups',
        'party-strengths',
        'parties-panachage',
    ):
        layout = ElectionCompoundLayout(self, request, tab=tab)
        layout.last_modified = last_modified
        if layout.visible:
            embed[tab].append(request.link(self, f'{tab}-chart'))
        if layout.svg_path:
            charts[tab] = request.link(self, f'{tab}-svg')

    for tab in ElectionCompoundLayout.tabs_with_embedded_tables:
        layout = ElectionCompoundLayout(self, request, tab=tab)
        if layout.visible and (table_link := layout.table_link()):
            embed[tab].append(table_link)

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
    superregions: dict[str, JSONObject]
    # NOTE: This ignore is only safe because we immediately mutate the one
    #       key that is not json serializable, this is efficient, but not
    #       type safe.
    superregions = get_superregions(self, request.app.principal)  # type:ignore
    for superregion in superregions.values():
        superregion['superregion'] = request.link(superregion['superregion'])

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
        'superregions': superregions,
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
        'related_link': self.related_link,
        'title': self.title_translations,
        'type': 'election_compound',
        'url': request.link(self),
        'embed': embed,
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='summary',
    permission=MaybePublic
)
def view_election_compound_summary(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the summary of the election compound as JSON. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_election_compound_summary(self, request)


@ElectionDayApp.pdf_file(
    model=ElectionCompound,
    name='pdf',
    permission=MaybePublic
)
def view_election_compound_pdf(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """ View the generated PDF. """

    layout = ElectionCompoundLayout(self, request)
    return {
        'path': layout.pdf_path,
        'name': normalize_for_url(self.title or '')
    }
