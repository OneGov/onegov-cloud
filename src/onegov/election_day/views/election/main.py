from __future__ import annotations

from collections import defaultdict
from morepath import redirect
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_connection_results
from onegov.election_day.utils.election.lists import get_list_results
from onegov.election_day.utils.parties import get_party_results
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=Election,
    request_method='HEAD',
    permission=MaybePublic
)
def view_election_head(
    self: Election,
    request: ElectionDayRequest
) -> None:

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.html(
    model=Election,
    permission=MaybePublic
)
def view_election(
    self: Election,
    request: ElectionDayRequest
) -> Response:

    """" The main view. """

    return redirect(ElectionLayout(self, request).main_view)


@ElectionDayApp.json(
    model=Election,
    name='json',
    permission=MaybePublic
)
def view_election_json(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """" The main view as JSON. """

    last_modified = self.last_modified
    assert last_modified is not None

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = defaultdict(list)
    charts: JSONObject = {}
    media: JSONObject = {'charts': charts}
    layout = ElectionLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    for tab in (
        'candidates',
        'candidate-by-entity',
        'candidate-by-district',
        'lists',
        'list-by-entity',
        'list-by-district',
        'connections',
        'lists-panachage',
        'party-strengths',
        'parties-panachage',
    ):
        layout = ElectionLayout(self, request, tab=tab)
        layout.last_modified = last_modified
        if layout.visible:
            embed[tab].append(request.link(self, f'{tab}-chart'))
        if layout.svg_path:
            charts[tab] = request.link(self, f'{tab}-svg')

    for tab in ElectionLayout.tabs_with_embedded_tables:
        layout = ElectionLayout(self, request, tab=tab)
        if layout.visible and (table_link := layout.table_link()):
            embed[tab].append(table_link)

    _years, parties = get_party_results(self, json_serializable=True)

    data: JSONObject = {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': last_modified.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.progress[0] or 0,
            'total': self.progress[1] or 0
        },
        'related_link': self.related_link,
        'title': self.title_translations,  # type:ignore[dict-item]
        'short_title': self.short_title_translations,  # type:ignore[dict-item]
        'type': 'election',
        'statistics': {
            'total': {
                'eligible_voters': self.eligible_voters,
                'received_ballots': self.received_ballots,
                'accounted_ballots': self.accounted_ballots,
                'blank_ballots': self.blank_ballots,
                'invalid_ballots': self.invalid_ballots,
                'accounted_votes': self.accounted_votes,
                'turnout': self.turnout,
            },
            'entities': [
                {
                    'eligible_voters': entity.eligible_voters,
                    'received_ballots': entity.received_ballots,
                    'accounted_ballots': entity.accounted_ballots,
                    'blank_ballots': entity.blank_ballots,
                    'invalid_ballots': entity.invalid_ballots,
                    'accounted_votes': entity.accounted_votes,
                    'turnout': entity.turnout,
                    'name': entity.name if entity.entity_id else 'Expats',
                    'district': entity.district if entity.entity_id else '',
                    'id': entity.entity_id,
                } for entity in self.results
            ],
        },
        'election_type': self.type,
        'url': request.link(self),
        'embed': embed,  # type:ignore[dict-item]
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }

    session = object_session(self)

    if self.type == 'majorz':
        if self.majority_type == 'absolute':
            data['absolute_majority'] = self.absolute_majority
        data['candidates'] = [
            {
                'family_name': candidate.family_name,
                'first_name': candidate.first_name,
                'elected': candidate.elected,
                'party': candidate.party,
                'votes': candidate.votes,
            } for candidate in get_candidates_results(self, session)
        ]

    if self.type == 'proporz':
        data['candidates'] = [
            {
                'family_name': candidate.family_name,
                'first_name': candidate.first_name,
                'elected': candidate.elected,
                'party': candidate.party,
                'votes': candidate.votes,
                'list_name': candidate.list_name,
                'list_list_id': candidate.list_id
            } for candidate in get_candidates_results(self, session)
        ]

        data['lists'] = [
            {
                'name': item[0],
                'votes': item[1],
                'id': item[2],
            } for item in get_list_results(self)
        ]

        data['list_connections'] = [
            {
                'id': connection[0],
                'votes': connection[1],
                'lists': [
                    {
                        'name': item[0],
                        'votes': item[1],
                        'id': item[2],
                    } for item in connection[2]
                ],
                'subconnections': [
                    {
                        'id': subconnection[0],
                        'votes': subconnection[1],
                        'lists': [
                            {
                                'name': item[0],
                                'votes': item[1],
                                'id': item[2],
                            } for item in subconnection[2]
                        ],
                    } for subconnection in connection[3]
                ],
            } for connection in get_connection_results(self, session)
        ]

        data['parties'] = parties

    return data


@ElectionDayApp.json(
    model=Election,
    name='summary',
    permission=MaybePublic
)
def view_election_summary(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the summary of the election as JSON. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_election_summary(self, request)


@ElectionDayApp.pdf_file(
    model=Election,
    name='pdf',
    permission=MaybePublic
)
def view_election_pdf(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """ View the generated PDF. """

    layout = ElectionLayout(self, request)
    return {
        'path': layout.pdf_path,
        'name': normalize_for_url(self.title or '')
    }
