from onegov.ballot import Candidate, Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import desc
from sqlalchemy.orm import object_session


@ElectionDayApp.json(model=Election, permission=Public, name='candidates')
def view_election_candidates(self, request):
    """" View the candidates as JSON. Used to for the candidates bar chart. """

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
        'results': [{
            'text': '{} {}'.format(candidate[0], candidate[1]),
            'value': candidate[3],
            'class': 'active' if candidate[2] else 'inactive'
        } for candidate in candidates.all()],
        'majority': majority,
        'title': self.title
    }


@ElectionDayApp.html(model=Election, permission=Public,
                     name='candidates-chart', template='embed.pt')
def view_election_candidates_chart(self, request):
    """" View the candidates as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('bar_chart')
    request.include('frame_resizer')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'bar': request.link(self, name='candidates')
        }
    }
