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

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'districts')
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='districts-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_districts_table(self, request):

    """" Displays the districts as standalone table. """

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'districts'),
        'type': 'election-compound-table',
        'scope': 'districts'
    }
