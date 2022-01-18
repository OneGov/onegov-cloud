from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=Election,
    name='statistics',
    template='election/statistics.pt',
    permission=Public
)
def view_election_statistics(self, request):

    """" The main view. """

    return {
        'election': self,
        'layout': ElectionLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=Election,
    name='statistics-table',
    template='embed.pt',
    permission=Public
)
def view_election_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'layout': ElectionLayout(self, request, 'statistics'),
        'type': 'election-table',
        'scope': 'statistics'
    }
