from morepath.request import Response
from onegov.ballot import Vote
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import VotesLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import handle_headerless_params


@ElectionDayApp.html(model=Vote, template='vote/data.pt',
                     name='data', permission=Public)
def view_vote_data(self, request):
    """" The main view. """

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request, 'data')
    }


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
