from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout


@ElectionDayApp.html(
    model=ElectionCompound,
    name='districts',
    template='election_compound/districts.pt',
    permission=Public
)
def view_election_compound_districts(self, request):

    """" The districts view. """

    layout = ElectionCompoundLayout(self, request, 'districts')

    return {
        'election_compound': self,
        'layout': layout
    }
