from __future__ import annotations

from morepath import redirect
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Ballot
from onegov.election_day.models import Vote
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.vote import get_ballot_data_by_district
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Vote,
    name='districts',
    template='vote/districts.pt',
    permission=MaybePublic
)
def view_vote_districts(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-districts',
    template='vote/districts.pt',
    permission=MaybePublic
)
def view_vote_districts_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'proposal-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-districts',
    template='vote/districts.pt',
    permission=MaybePublic
)
def view_vote_districts_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (counter-proposal). """

    layout = VoteLayout(self, request, 'counter-proposal-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-districts',
    template='vote/districts.pt',
    permission=MaybePublic
)
def view_vote_districts_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view (tie-breaker). """

    layout = VoteLayout(self, request, 'tie-breaker-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-districts-map',
    permission=MaybePublic
)
def view_vote_districts_map_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-districts-map',
    permission=MaybePublic
)
def view_vote_districts_map_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-districts-map',
    permission=MaybePublic
)
def view_vote_districts_map_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the map of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-map',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Ballot,
    name='districts-table',
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
        'layout': VoteLayout(self.vote, request, f'{self.type}-districts'),
        'type': 'ballot-table',
        'year': self.vote.date.year,
        'scope': 'districts',
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-districts-table',
    permission=MaybePublic
)
def view_vote_districts_table_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table by districts of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-districts-table',
    permission=MaybePublic
)
def view_vote_districts_table_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table by districts of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-districts-table',
    permission=MaybePublic
)
def view_vote_districts_table_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> Response:
    """ A static link to the table of the tie breaker by districts. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='districts-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.json(
    model=Ballot,
    name='by-district',
    permission=MaybePublic
)
def view_ballot_by_district(
    self: Ballot,
    request: ElectionDayRequest
) -> JSON_ro:
    """ Returns the data for the ballot map. """

    return get_ballot_data_by_district(self)  # type:ignore[return-value]


@ElectionDayApp.html(
    model=Ballot,
    name='districts-map',
    template='embed.pt',
    permission=MaybePublic
)
def view_ballot_districts_as_map(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:
    """" View the results of the districts of ballot as map. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.vote.last_modified)

    layout = VoteLayout(self.vote, request, f'{self.type}-districts')

    return {
        'model': self,
        'layout': layout,
        'type': 'map',
        'scope': 'districts',
        'year': self.vote.date.year,
        'thumbs': 'true',
        'color_scale': 'rb',
        'label_left_hand': layout.label('Nay'),
        'label_right_hand': layout.label('Yay'),
        'data_url': request.link(self, name='by-district'),
    }


@ElectionDayApp.svg_file(
    model=Ballot,
    name='districts-map-svg',
    permission=MaybePublic
)
def view_ballot_districts_svg(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:

    """" Download the results of the districts of ballot as a SVG. """

    layout = VoteLayout(
        self.vote, request, tab='{}-districts'.format(self.type)
    )
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
