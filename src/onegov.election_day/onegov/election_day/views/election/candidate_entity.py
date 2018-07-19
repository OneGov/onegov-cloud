from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import func


def candidate_options(request, election):
    elected = request.translate(_("Elected")).lower()
    return [
        (
            request.link(candidate_, name='by-entity'),
            '{} {}'.format(
                f'{candidate_.family_name} {candidate_.first_name}',
                (f'({elected})' if candidate_.elected else '')
            ).strip()
        )
        for candidate_ in election.candidates.order_by(None).order_by(
            Candidate.elected.desc(),
            func.lower(Candidate.family_name),
            func.lower(Candidate.first_name),
        )
    ]


@ElectionDayApp.json(
    model=Candidate,
    name='by-entity',
    permission=Public
)
def view_candidate_by_entity(self, request):

    """" View the candidate by entity as JSON. """

    return self.percentage_by_entity


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-entity',
    template='election/heatmap.pt',
    permission=Public
)
def view_election_candidate_by_entity(self, request):

    """" View the candidate as heatmap by entity. """

    layout = ElectionLayout(self, request, 'candidate-by-entity')

    options = candidate_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'entities',
        'data_url': data_url,
        'embed_source': request.link(self, name='candidate-by-entity-chart')
    }


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-entity-chart',
    template='embed.pt',
    permission=Public
)
def view_election_candidate_by_entity_chart(self, request):

    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    options = candidate_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'map',
        'scope': 'entities',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'r',
        'label_left_hand': '0%',
        'label_right_hand': '100%',
        'data_url': data_url,
        'options': options
    }
