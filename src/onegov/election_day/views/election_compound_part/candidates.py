from onegov.ballot import ElectionCompoundPart
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_elected_candidates


def get_districts(model, layout):
    return {
        election.id: (
            election.domain_segment,
            layout.request.link(election),
            election.domain_supersegment,
        )
        for election in layout.model.elections
    }


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='candidates',
    template='election_compound_part/candidates.pt',
    permission=Public
)
def view_election_compound_part_candidates(self, request):

    """" The main view. """

    session = request.app.session()
    layout = ElectionCompoundPartLayout(self, request, 'candidates')

    return {
        'election_compound_part': self,
        'elected_candidates': get_elected_candidates(self, session).all(),
        'districts': get_districts(self, layout),
        'layout': layout
    }


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    name='candidates-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_part_statistics_table(self, request):

    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    session = request.app.session()
    layout = ElectionCompoundPartLayout(self, request, 'candidates')

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session).all(),
        'districts': get_districts(self, layout),
        'layout': layout,
        'type': 'election-compound-table',
        'scope': 'candidates'
    }
