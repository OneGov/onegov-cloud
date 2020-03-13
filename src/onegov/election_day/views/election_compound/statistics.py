from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout


@ElectionDayApp.html(
    model=ElectionCompound,
    name='statistics',
    template='election_compound/statistics.pt',
    permission=Public
)
def view_election_statistics(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'statistics')

    return {
        'election_compound': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='statistics-table',
    template='embed.pt',
    permission=Public
)
def view_election_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    layout = ElectionCompoundLayout(self, request, 'statistics')

    return {
        'election_compound': self,
        'layout': layout,
        'type': 'election-compound-table',
        'scope': 'statistics'
    }
