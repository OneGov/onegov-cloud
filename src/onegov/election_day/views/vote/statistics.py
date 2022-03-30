from morepath import redirect
from onegov.ballot import Ballot
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header
from webob.exc import HTTPNotFound


@ElectionDayApp.html(
    model=Vote,
    name='statistics',
    template='vote/statistics.pt',
    permission=Public
)
def view_vote_statistics(self, request):

    """" The statistics view (simple vote). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-statistics',
    template='vote/statistics.pt',
    permission=Public
)
def view_vote_statistics_proposal(self, request):

    """" The statistics view (proposal). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'proposal-statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-statistics',
    template='vote/statistics.pt',
    permission=Public
)
def view_vote_statistics_counter_proposal(self, request):

    """" The statistics view (counter-proposal). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'counter-proposal-statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-statistics',
    template='vote/statistics.pt',
    permission=Public
)
def view_vote_statistics_tie_breaker(self, request):

    """" The statistics view (tie-breaker). """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'tie-breaker-statistics')
    }


@ElectionDayApp.html(
    model=Ballot,
    name='statistics-table',
    template='embed.pt',
    permission=Public
)
def view_ballot_as_statistics_table(self, request):

    """" View the statistics of the entities of ballot as table. """

    @request.after
    def add_last_modified(response):
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
    permission=Public
)
def view_vote_statistics_table_proposal(self, request):

    """ A static link to the statistics table of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='statistics-table'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-statistics-table',
    permission=Public
)
def view_vote_statistics_table_counter_proposal(self, request):

    """ A static link to the statistics table of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='statistics-table'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-statistics-table',
    permission=Public
)
def view_vote_statistics_table_tie_breaker(self, request):

    """ A static link to the statistics table of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(request.link(ballot, name='statistics-table'))

    raise HTTPNotFound()
