from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.parties import get_parties_panachage_data


@ElectionDayApp.json(
    model=Election,
    name='parties-panachage-data',
    permission=Public
)
def view_election_parties_panachage_data(self, request):

    """" View the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    return get_parties_panachage_data(self, request)


@ElectionDayApp.html(
    model=Election,
    name='parties-panachage-chart',
    template='embed.pt',
    permission=Public
)
def view_election_parties_panachage_chart(self, request):

    """" View the panachage data as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'parties-panachage-chart',
    }


@ElectionDayApp.html(
    model=Election,
    name='parties-panachage',
    template='election/parties_panachage.pt',
    permission=Public
)
def view_election_parties_panachage(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'parties-panachage')

    return {
        'election': self,
        'layout': layout
    }


@ElectionDayApp.svg_file(model=Election, name='parties-panachage-svg')
def view_election_parties_panachage_svg(self, request):

    """ View the panachage as SVG. """

    layout = ElectionLayout(self, request, 'parties-panachage')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
