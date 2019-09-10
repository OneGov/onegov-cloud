from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils.election import get_elected_candidates


def get_districts(model, request):
    return {
        election.id: (election.district, request.link(election))
        for election in model.elections if election.results.first()
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates',
    template='election_compound/candidates.pt',
    permission=Public
)
def view_election_compound_candidates(self, request):

    """" The main view. """

    session = request.app.session()

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session),
        'districts': get_districts(self, request),
        'layout': ElectionCompoundLayout(self, request, 'candidates')
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates-table',
    template='embed.pt',
    permission=Public
)
def view_election_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    session = request.app.session()

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session),
        'districts': get_districts(self, request),
        'layout': ElectionCompoundLayout(self, request, 'candidates'),
        'type': 'election-compound-table',
        'scope': 'candidates'
    }
