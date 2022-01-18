from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=ElectionCompound,
    name='statistics',
    template='election_compound/statistics.pt',
    permission=Public
)
def view_election_statistics(self, request):

    """" The main view. """

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=ElectionCompound,
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
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'statistics'),
        'type': 'election-compound-table',
        'scope': 'statistics'
    }
