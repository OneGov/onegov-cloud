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
            request.link(candidate_, name='by-district'),
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
    name='by-district',
    permission=Public
)
def view_candidate_by_district(self, request):

    """" View the candidate by district as JSON. """

    return self.percentage_by_district


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-district',
    template='election/heatmap.pt',
    permission=Public
)
def view_election_candidate_by_district(self, request):

    """" View the candidate as heatmap by district. """

    layout = ElectionLayout(self, request, 'candidate-by-district')

    options = candidate_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'districts',
        'data_url': data_url,
        'embed_source': request.link(self, name='candidate-by-district-chart')
    }


@ElectionDayApp.html(
    model=Election,
    name='candidate-by-district-chart',
    template='embed.pt',
    permission=Public
)
def view_election_candidate_by_district_chart(self, request):

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
        'scope': 'districts',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'r',
        'label_left_hand': '0%',
        'label_right_hand': '100%',
        'data_url': data_url,
        'options': options
    }
