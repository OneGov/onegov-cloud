from morepath.request import Response
from onegov.ballot import Candidate, Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.views.election import get_candidates_results
from sqlalchemy import desc
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

    session = object_session(self)

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes
    )
    candidates = candidates.order_by(
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == self.id)

    majority = 0
    if self.type == 'majorz' and self.absolute_majority is not None:
        majority = self.absolute_majority

    return {
        'results': [
            {
                'text': '{} {}'.format(candidate[0], candidate[1]),
                'value': candidate[3],
                'class': 'active' if candidate[2] else 'inactive'
            } for candidate in candidates.all()
            if self.type == 'majorz' or self.type == 'proporz' and candidate[2]
        ],
        'majority': majority,
        'title': self.title
    }


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
        'data': {
            'bar': request.link(self, name='candidates-data')
        }
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


@ElectionDayApp.json(
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
