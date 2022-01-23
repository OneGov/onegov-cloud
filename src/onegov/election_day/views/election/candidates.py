from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.hidden_by_principal import \
    hide_candidates_chart
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_parameter
from onegov.election_day.utils.election import get_candidates_data
from onegov.election_day.utils.election import get_candidates_results
from sqlalchemy.orm import object_session
from onegov.election_day import _

election_incomplete_text = _(
    'The figure with elected candidates will be available '
    'as soon the final results are published.'
)


@ElectionDayApp.json(
    model=Election,
    name='candidates-data',
    permission=Public
)
def view_election_candidates_data(self, request):

    """" View the candidates as JSON.

    Used to for the candidates bar chart.

    """

    limit = get_parameter(request, 'limit', int, None)
    lists = get_parameter(request, 'lists', list, None)
    elected = get_parameter(request, 'elected', bool, None)

    return get_candidates_data(self, limit=limit, lists=lists, elected=elected)


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
        'skip_rendering': hide_candidates_chart(self, request),
        'help_text': election_incomplete_text,
        'model': self,
        'layout': ElectionLayout(self, request),
        'type': 'candidates-chart',
    }


@ElectionDayApp.html(
    model=Election,
    name='candidates',
    template='election/candidates.pt',
    permission=Public
)
def view_election_candidates(self, request):

    """" The main view. """

    return {
        'skip_rendering': hide_candidates_chart(self, request),
        'help_text': election_incomplete_text,
        'election': self,
        'layout': ElectionLayout(self, request, 'candidates'),
        'candidates': get_candidates_results(self, object_session(self))
    }


@ElectionDayApp.html(
    model=Election,
    name='candidates-table',
    template='embed.pt',
    permission=Public
)
def view_election_lists_table(self, request):

    """" View the lists as table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'candidates': get_candidates_results(self, object_session(self)).all(),
        'layout': ElectionLayout(self, request, 'candidates'),
        'type': 'election-table',
        'scope': 'candidates',
    }


@ElectionDayApp.svg_file(model=Election, name='candidates-svg')
def view_election_candidates_svg(self, request):

    """ View the candidates as SVG. """

    layout = ElectionLayout(self, request, 'candidates')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
