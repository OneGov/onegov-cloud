from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout


@ElectionDayApp.html(
    model=Election,
    name='statistics',
    template='election/statistics.pt',
    permission=Public
)
def view_election_statistics(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'statistics')

    return {
        'election': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Election,
    name='statistics-table',
    template='embed.pt',
    permission=Public
)
def view_election_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    layout = ElectionLayout(self, request, 'statistics')

    return {
        'election': self,
        'layout': layout,
        'type': 'election-table',
        'scope': 'statistics'
    }
