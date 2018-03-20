from morepath.request import Response
from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.views.election.parties import get_party_results
from onegov.election_day.views.election.parties import get_party_results_data
from onegov.election_day.views.election.parties import get_party_results_deltas


@ElectionDayApp.json(
    model=ElectionCompound,
    name='parties-data',
    permission=Public
)
def view_election_compound_parties_data(self, request):

    """ Retuns the data used for the grouped bar diagram showing the party
    results.

    """

    return get_party_results_data(self)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties-chart',
    template='embed.pt',
    permission=Public
)
def view_election_compound_parties_chart(self, request):

    """" View the parties as grouped bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'grouped_bar': request.link(self, name='parties-data')
        }
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties',
    template='election_compound/parties.pt',
    permission=Public
)
def view_election_compound_parties(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'parties')

    years, parties = get_party_results(self)
    deltas, results = get_party_results_deltas(self, years, parties)

    return {
        'election_compound': self,
        'layout': layout,
        'results': results,
        'years': years,
        'deltas': deltas
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='parties-svg',
    permission=Public
)
def view_election_compound_parties_svg(self, request):

    """ View the parties as SVG. """

    layout = ElectionCompoundLayout(self, request, 'parties')
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
