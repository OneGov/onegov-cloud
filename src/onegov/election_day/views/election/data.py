from onegov.ballot import Election
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_connection_results_api
from onegov.election_day.utils.election.lists import \
    get_aggregated_list_results


@ElectionDayApp.html(
    model=Election,
    name='data',
    template='election/data.pt',
    permission=Public
)
def view_election_data(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'data')

    return {
        'election': self,
        'layout': layout
    }


@ElectionDayApp.json_file(model=Election, name='data-json')
def view_election_data_as_json(self, request):

    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export(consider_completed=True),
        'name': normalize_for_url(self.title)
    }


@ElectionDayApp.csv_file(model=Election, name='data-csv')
def view_election_data_as_csv(self, request):

    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export(),
        'name': normalize_for_url(self.title)
    }


@ElectionDayApp.csv_file(model=Election, name='data-parties')
def view_election_parties_data_as_csv(self, request):

    """ View the raw parties data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export_parties(),
        'name': normalize_for_url(
            '{}-{}'.format(
                self.title,
                request.translate(_("Parties")).lower()
            )
        )
    }


@ElectionDayApp.json(
    model=Election,
    name='data-aggregated-lists',
    permission=Public
)
def view_election_aggregated_lists_data(self, request):

    """" View the lists as JSON. """

    return get_aggregated_list_results(self, request.session)


@ElectionDayApp.json(
    model=Election,
    name='data-list-connections',
    permission=Public
)
def view_election_aggregated_connections_data(self, request):

    """" View the list connections as JSON. """

    return get_connection_results_api(self, request.session)
