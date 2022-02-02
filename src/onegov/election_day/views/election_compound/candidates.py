from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_elected_candidates


def get_districts(model, layout):
    return {
        election.id: (
            election.domain_segment,
            layout.request.link(election)
        )
        for election in layout.model.elections
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
    layout = ElectionCompoundLayout(self, request, 'candidates')

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session),
        'districts': get_districts(self, layout),
        'layout': layout
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates-table',
    template='embed.pt',
    permission=Public
)
def view_election_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    session = request.app.session()
    layout = ElectionCompoundLayout(self, request, 'candidates')

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session),
        'districts': get_districts(self, layout),
        'layout': layout,
        'type': 'election-compound-table',
        'scope': 'candidates'
    }
