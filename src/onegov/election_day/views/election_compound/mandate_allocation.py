from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils.election import get_party_results
from onegov.election_day.utils.election import get_party_results_deltas


@ElectionDayApp.html(
    model=ElectionCompound,
    name='mandate-allocation',
    template='election_compound/mandate_allocation.pt',
    permission=Public
)
def view_election_compound_mandate_allocation(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'mandate-allocation')

    years, parties = get_party_results(self)
    deltas, results = get_party_results_deltas(self, years, parties)

    return {
        'election_compound': self,
        'layout': layout,
        'results': results,
        'years': years,
        'deltas': deltas
    }
