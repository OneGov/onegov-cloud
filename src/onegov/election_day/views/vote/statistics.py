from __future__ import annotations

from morepath import redirect
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Ballot
from onegov.election_day.models import Vote
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Vote,
    name='statistics',
    template='vote/statistics.pt',
    permission=MaybePublic
)
def view_vote_statistics(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The statistics view (simple vote). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-statistics',
    template='vote/statistics.pt',
    permission=MaybePublic
)
def view_vote_statistics_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The statistics view (proposal). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'proposal-statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-statistics',
    template='vote/statistics.pt',
    permission=MaybePublic
)
def view_vote_statistics_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The statistics view (counter-proposal). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'counter-proposal-statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-statistics',
    template='vote/statistics.pt',
    permission=MaybePublic
)
def view_vote_statistics_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The statistics view (tie-breaker). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'tie-breaker-statistics')
    }


@ElectionDayApp.html(
    model=Ballot,
    name='statistics-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_ballot_as_statistics_table(
    self: Ballot,
    request: ElectionDayRequest
) -> RenderData:
    """" View the statistics of the entities of ballot as table. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.vote.last_modified)

    return {
        'ballot': self,
        'layout': VoteLayout(self.vote, request, f'{self.type}-entities'),
        'type': 'ballot-table',
        'year': self.vote.date.year,
        'scope': 'statistics',
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-statistics-table',
    permission=MaybePublic
)
def view_vote_statistics_table_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:

    """ A static link to the statistics table of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='statistics-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-statistics-table',
    permission=MaybePublic
)
def view_vote_statistics_table_counter_proposal(
    self: Vote,
    request: ElectionDayRequest
) -> Response:

    """ A static link to the statistics table of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='statistics-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-statistics-table',
    permission=MaybePublic
)
def view_vote_statistics_table_tie_breaker(
    self: Vote,
    request: ElectionDayRequest
) -> Response:

    """ A static link to the statistics table of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(
            request.link(
                ballot,
                name='statistics-table',
                query_params=dict(request.GET)
            )
        )

    raise HTTPNotFound()
