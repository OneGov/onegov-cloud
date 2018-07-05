from morepath.request import Response
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout, ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_party_results
from onegov.election_day.utils.election import get_party_results_data
from onegov.election_day.utils.election import get_party_results_deltas


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
        'layout': DefaultLayout(self, request),
        'type': 'grouped-bar',
        'data_url': request.link(self, name='party-strengths-data'),
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


@ElectionDayApp.view(
    model=Election,
    name='party-strengths-svg',
    permission=Public
)
def view_election_party_strengths_svg(self, request):

    """ View the party strengths as SVG. """

    layout = ElectionLayout(self, request, 'party-strengths')
    if not layout.svg_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.svg_path, 'r') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/svg; charset=utf-8',
        content_disposition='inline; filename={}'.format(layout.svg_name)
    )
