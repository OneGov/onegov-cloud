from __future__ import annotations

from collections import defaultdict
from morepath import redirect
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Vote
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary

from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from onegov.election_day.types import TitleJson
    from onegov.election_day.types import VoteJson
    from webob.response import Response


@ElectionDayApp.view(
    model=Vote,
    request_method='HEAD',
    permission=MaybePublic
)
def view_vote_head(
    self: Vote,
    request: ElectionDayRequest
) -> None:

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.html(
    model=Vote,
    permission=MaybePublic
)
def view_vote(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """" The main view. """

    return redirect(VoteLayout(self, request).main_view)


@ElectionDayApp.json(
    model=Vote,
    name='json',
    permission=MaybePublic
)
def view_vote_json(
    self: Vote,
    request: ElectionDayRequest
) -> VoteJson:
    """" The main view as JSON. """

    last_modified = self.last_modified
    assert last_modified is not None

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = defaultdict(list)
    media: JSONObject = {}
    layout = VoteLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    if layout.show_map:
        media['maps'] = maps = {}
        for tab in (
            'entities',
            'proposal-entities',
            'counter-proposal-entities',
            'tie-breaker-entities',
            'districts',
            'proposal-districts',
            'counter-proposal-districts',
            'tie-breaker-districts'
        ):
            layout = VoteLayout(self, request, tab)
            layout.last_modified = last_modified
            if layout.visible:
                embed[tab].append(layout.map_link)
                if layout.svg_path:
                    maps[tab] = layout.svg_link

    embed['entities'].append(request.link(self, name='vote-header-widget'))

    for tab in layout.tabs_with_embedded_tables:
        layout = VoteLayout(self, request, tab)
        if layout.visible:
            embed[tab].append(layout.table_link())

    counted = self.progress[0]
    nays_percentage = self.nays_percentage if counted else None
    yeas_percentage = self.yeas_percentage if counted else None
    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': last_modified.isoformat(),
        'progress': {
            'counted': counted,
            'total': self.progress[1]
        },
        'related_link': self.related_link,
        'title': cast('TitleJson', self.title_translations),
        'short_title': cast('TitleJson', self.short_title_translations),
        'type': 'vote',
        'results': {
            'answer': self.answer,
            'nays_percentage': nays_percentage,
            'yeas_percentage': yeas_percentage,
        },
        'ballots': [
            {
                'type': ballot.type,
                'title': cast('TitleJson', ballot.title_translations),
                'progress': {
                    'counted': ballot.progress[0],
                    'total': ballot.progress[1],
                },
                'results': {
                    'total': {
                        'accepted': ballot.accepted,
                        'yeas': ballot.yeas,
                        'nays': ballot.nays,
                        'empty': ballot.empty,
                        'invalid': ballot.invalid,
                        'yeas_percentage': ballot.yeas_percentage,
                        'nays_percentage': ballot.nays_percentage,
                        'eligible_voters': ballot.eligible_voters,
                        'cast_ballots': ballot.cast_ballots,
                        'turnout': ballot.turnout,
                        'counted': ballot.counted,
                    },
                    'entities': [
                        {
                            'accepted': entity.accepted,
                            'yeas': entity.yeas,
                            'nays': entity.nays,
                            'empty': entity.empty,
                            'invalid': entity.invalid,
                            'yeas_percentage': entity.yeas_percentage,
                            'nays_percentage': entity.nays_percentage,
                            'eligible_voters': entity.eligible_voters,
                            'cast_ballots': entity.cast_ballots,
                            'turnout': entity.turnout,
                            'counted': entity.counted,
                            'name': (
                                entity.name if entity.entity_id else 'Expats'
                            ),
                            'district': (
                                entity.district or ''
                                if entity.entity_id else ''
                            ),
                            'id': entity.entity_id,
                        } for entity in ballot.results
                    ],
                },
            } for ballot in self.ballots
        ],
        'url': request.link(self),
        'embed': cast('JSONObject', embed),
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }


@ElectionDayApp.json(
    model=Vote,
    name='summary',
    permission=MaybePublic
)
def view_vote_summary(
    self: Vote,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the summary of the vote as JSON. """

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_vote_summary(self, request)


@ElectionDayApp.pdf_file(
    model=Vote,
    name='pdf',
    permission=MaybePublic
)
def view_vote_pdf(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """ View the generated PDF. """

    layout = VoteLayout(self, request)
    return {
        'path': layout.pdf_path,
        'name': normalize_for_url(self.title or '')
    }


@ElectionDayApp.html(
    model=Vote,
    name='vote-header-widget',
    permission=MaybePublic,
    template='embed.pt'
)
def view_vote_header_as_widget(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """ A static link to the top bar showing the vote result as widget. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'vote': self,
        'layout': VoteLayout(self, request),
        'type': 'vote-header',
        'scope': 'vote',
    }
