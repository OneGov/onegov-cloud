from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils.election import get_elected_candidates


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates',
    template='election_compound/candidates.pt',
    permission=Public
)
def view_election_compound_candidates(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'candidates')

    session = request.app.session()
    elected_candidates = get_elected_candidates(self, session)
    districts = {
        election.id: (
            election.results.first().district or election.results.first().name,
            request.link(election)
        )
        for election in self.elections if election.results.first()
    }

    return {
        'election_compound': self,
        'elected_candidates': elected_candidates,
        'districts': districts,
        'layout': layout
    }
