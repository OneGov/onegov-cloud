from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=Vote,
    name='statistics',
    template='vote/statistics.pt',
    permission=Public
)
def view_vote_statistics(self, request):

    """" The main view. """

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=Vote,
    name='statistics-table',
    template='embed.pt',
    permission=Public
)
def view_vote_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'vote': self,
        'layout': VoteLayout(self, request, 'statistics'),
        'type': 'vote-table',
        'scope': 'statistics'
    }


# todo: proposal, counter_proposal, tie_breaker, embeds?
