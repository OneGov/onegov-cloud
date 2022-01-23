from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_data
from onegov.election_day.utils.parties import get_party_results_deltas


@ElectionDayApp.json(
    model=Election,
    name='party-strengths-data',
    permission=Public
)
def view_election_party_strengths_data(self, request):

    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    return get_party_results_data(self)


@ElectionDayApp.html(
    model=Election,
    name='party-strengths-chart',
    template='embed.pt',
    permission=Public
)
def view_election_party_strengths_chart(self, request):

    """" View the party strengths as grouped bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'party-strengths-chart',
    }


@ElectionDayApp.html(
    model=Election,
    name='party-strengths',
    template='election/party_strengths.pt',
    permission=Public
)
def view_election_party_strengths(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'party-strengths')

    years, parties = get_party_results(self)
    deltas, results = get_party_results_deltas(self, years, parties)

    return {
        'election': self,
        'layout': layout,
        'results': results,
        'years': years,
        'deltas': deltas
    }


@ElectionDayApp.svg_file(model=Election, name='party-strengths-svg')
def view_election_party_strengths_svg(self, request):

    """ View the party strengths as SVG. """

    layout = ElectionLayout(self, request, 'party-strengths')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
