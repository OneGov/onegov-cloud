from morepath import redirect
from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_compound_summary


@ElectionDayApp.html(
    model=ElectionCompound,
    permission=Public
)
def view_election_compound(self, request):

    """" The main view. """

    return redirect(ElectionCompoundLayout(self, request).main_view)


@ElectionDayApp.json(
    model=ElectionCompound,
    name='json',
    permission=Public
)
def view_election_compound_json(self, request):
    """" The main view as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'last_modified': self.last_modified.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.progress[0] or 0,
            'total': self.progress[1] or 0
        },
        'elections': [
            request.link(election) for election in self.elections
        ],
        'elected_candidates': self.elected_candidates,
        'related_link': self.related_link,
        'title': self.title_translations,
        'type': 'election_compound',
        'url': request.link(self),
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
            'xlsx': request.link(self, 'data-xlsx'),
        }
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='summary',
    permission=Public
)
def view_election_compound_summary(self, request):

    """ View the summary of the election compound as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return get_election_compound_summary(self, request)
