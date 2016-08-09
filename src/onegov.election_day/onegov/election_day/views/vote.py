from morepath.request import Response
from onegov.ballot import Ballot, Vote
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote(self, request):
    """" The main view. """

    layout = DefaultLayout(self, request)
    request.include('ballot_map')

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return {
        'vote': self,
        'layout': layout,
        'counted': self.counted
    }


@ElectionDayApp.json(model=Ballot, permission=Public, name='by-municipality')
def view_ballot_by_municipality(self, request):
    return self.percentage_by_municipality()


# TODO: as_json

@ElectionDayApp.json(model=Vote, permission=Public, name='summary')
def view_vote_summary(self, request):
    """ View the summary of the vote as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_vote_summary(self, request)


@ElectionDayApp.json(model=Vote, name='data-json', permission=Public)
def view_vote_data_as_json(self, request):
    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return self.export()


@ElectionDayApp.view(model=Vote, name='data-csv', permission=Public)
def view_vote_data_as_csv(self, request):
    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Vote, name='data-xlsx', permission=Public)
def view_vote_data_as_xlsx(self, request):
    """ View the raw data as XLSX. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return Response(
        convert_list_of_dicts_to_xlsx(self.export()),
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename={}.xlsx'.format(
            normalize_for_url(self.title)
        )
    )
