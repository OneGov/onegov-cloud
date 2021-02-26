from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=Vote,
    name='data',
    template='vote/data.pt',
    permission=Public
)
def view_vote_data(self, request):

    """" The main view. """

    layout = VoteLayout(self, request, 'data')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.json_file(model=Vote, name='data-json')
def view_vote_data_as_json(self, request):

    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export(),
        'name': normalize_for_url(self.title)
    }


@ElectionDayApp.csv_file(model=Vote, name='data-csv')
def view_vote_data_as_csv(self, request):

    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export(),
        'name': normalize_for_url(self.title)
    }
