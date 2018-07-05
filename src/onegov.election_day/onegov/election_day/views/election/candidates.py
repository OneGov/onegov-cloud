from morepath.request import Response
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results
from sqlalchemy.orm import object_session


@ElectionDayApp.json(
    model=Election,
    name='candidates-data',
    permission=Public
)
def view_election_candidates_data(self, request):

    """" View the candidates as JSON.

    Used to for the candidates bar chart.

    """

    return get_candidates_data(self, request)


@ElectionDayApp.html(
    model=Election,
    name='candidates-chart',
    template='embed.pt',
    permission=Public
)
def view_election_candidates_chart(self, request):

    """" View the candidates as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'bar',
        'data_url': request.link(self, name='candidates-data'),
    }


@ElectionDayApp.html(
    model=Election,
    name='candidates',
    template='election/candidates.pt',
    permission=Public
)
def view_election_candidates(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'candidates')

    return {
        'election': self,
        'layout': layout,
        'candidates': get_candidates_results(self, object_session(self)).all()
    }


@ElectionDayApp.view(
    model=Election,
    name='candidates-svg',
    permission=Public
)
def view_election_candidates_svg(self, request):

    """ View the candidates as SVG. """

    layout = ElectionLayout(self, request, 'candidates')
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
