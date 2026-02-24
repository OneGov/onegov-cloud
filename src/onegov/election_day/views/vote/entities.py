from __future__ import annotations

from morepath import redirect
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Ballot
from onegov.election_day.models import Vote
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.vote import get_ballot_data_by_entity
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Vote,
    name='entities',
    template='vote/entities.pt',
    permission=MaybePublic
)
def view_vote_entities(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-entities',
    template='vote/entities.pt',
    permission=MaybePublic
)
def view_vote_entities_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'proposal-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-entities',
    template='vote/entities.pt',
    permission=MaybePublic
)
def view_vote_entities_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (counter-proposal). """

    layout = VoteLayout(self, request, 'counter-proposal-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-entities',
    template='vote/entities.pt',
    permission=MaybePublic
)
def view_vote_entities_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (tie-breaker). """

    layout = VoteLayout(self, request, 'tie-breaker-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-entities-map',
    permission=MaybePublic
)
def view_vote_entities_map_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-entities-map',
    permission=MaybePublic
)
def view_vote_entities_map_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-entities-map',
    permission=MaybePublic
)
def view_vote_entities_map_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.json(
    model=Ballot,
    name='by-entity',
    permission=MaybePublic
)
def view_ballot_by_entity(
    self: Ballot,
    request: ElectionDayRequest
) -> JSON_ro:
    """ Returns the data for the ballot map. """

    return get_ballot_data_by_entity(self)  # type:ignore[return-value]


@ElectionDayApp.html(
    model=Ballot,
    name='entities-map',
    template='embed.pt',
    permission=MaybePublic
)
def view_ballot_entities_as_map(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:
    """" View the results of the entities of ballot as map. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.vote.last_modified)

    layout = VoteLayout(self.vote, request, f'{self.type}-entities')

    return {
        'model': self,
        'layout': layout,
        'type': 'map',
        'scope': 'entities',
        'year': self.vote.date.year,
        'thumbs': 'true',
        'color_scale': 'rb',
        'label_left_hand': layout.label('Nay'),
        'label_right_hand': layout.label('Yay'),
        'data_url': request.link(self, name='by-entity'),
    }


@ElectionDayApp.html(
    model=Ballot,
    name='entities-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_ballot_as_table(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:
    """" View the results of the entities of ballot as table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.vote.last_modified)

    return {
        'ballot': self,
        'layout': VoteLayout(self.vote, request, f'{self.type}-entities'),
        'type': 'ballot-table',
        'year': self.vote.date.year,
        'scope': 'entities',
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-entities-table',
    permission=MaybePublic
)
def view_vote_entities_table_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table by entities of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-entities-table',
    permission=MaybePublic
)
def view_vote_entities_table_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table by entities of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-entities-table',
    permission=MaybePublic
)
def view_vote_entities_table_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='entities-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.svg_file(
    model=Ballot,
    name='entities-map-svg',
    permission=MaybePublic
)
def view_ballot_entities_svg(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:
    """ Download the results of the entities of ballot as a SVG. """

    layout = VoteLayout(
        self.vote, request, tab=f'{self.type}-entities'
    )
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
