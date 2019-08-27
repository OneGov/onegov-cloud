from morepath.request import Response
from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_parties_panachage_data


@ElectionDayApp.json(
    model=ElectionCompound,
    name='parties-panachage-data',
    permission=Public
)
def view_election_compound_parties_panachage_data(self, request):

    """" View the panachage data as JSON. Used to for the panachage sankey
    chart.

    """

    return get_parties_panachage_data(self, request)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties-panachage-chart',
    template='embed.pt',
    permission=Public
)
def view_election_compound_parties_panachage_chart(self, request):

    """" View the panachage data as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'sankey',
        'inverse': 'false',
        'data_url': request.link(self, name='parties-panachage-data'),
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='parties-panachage',
    template='election_compound/parties_panachage.pt',
    permission=Public
)
def view_election_compound_parties_panachage(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'parties-panachage')

    return {
        'election_compound': self,
        'layout': layout
    }


@ElectionDayApp.view(
    model=ElectionCompound,
    name='parties-panachage-svg',
    permission=Public
)
def view_election_compound_parties_panachage_svg(self, request):

    """ View the panachage as SVG. """

    layout = ElectionCompoundLayout(self, request, 'parties-panachage')
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
