from collections import OrderedDict
from morepath.request import Response
from onegov.ballot import Election
from onegov.ballot import PartyResult
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.custom import json
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header


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


@ElectionDayApp.view(
    model=Election,
    name='data-json',
    permission=Public
)
def view_election_data_as_json(self, request):

    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return Response(
        json.dumps(self.export(), sort_keys=True, indent=2).encode('utf-8'),
        content_type='application/json',
        content_disposition='inline; filename={}.json'.format(
            normalize_for_url(self.title)
        )
    )


@ElectionDayApp.view(
    model=Election,
    name='data-csv',
    permission=Public
)
def view_election_data_as_csv(self, request):

    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return Response(
        convert_list_of_dicts_to_csv(self.export()),
        content_type='text/csv',
        content_disposition='inline; filename={}.csv'.format(
            normalize_for_url(self.title)
        )
    )


@ElectionDayApp.view(
    model=Election,
    name='data-xlsx',
    permission=Public
)
def view_election_data_as_xlsx(self, request):

    """ View the raw data as XLSX. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return Response(
        convert_list_of_dicts_to_xlsx(self.export()),
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename={}.xlsx'.format(
            normalize_for_url(self.title)
        )
    )


@ElectionDayApp.view(
    model=Election,
    name='data-parties',
    permission=Public
)
def view_election_parties_data_as_csv(self, request):

    """ View the raw parties data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    results = self.party_results.order_by(
        PartyResult.year.desc(),
        PartyResult.name
    )

    rows = []
    for result in results:
        row = OrderedDict()
        row['year'] = result.year
        row['total_votes'] = result.total_votes
        row['name'] = result.name
        row['color'] = result.color
        row['mandates'] = result.number_of_mandates
        row['votes'] = result.votes
        rows.append(row)

    return Response(
        convert_list_of_dicts_to_csv(rows),
        content_type='text/csv',
        content_disposition='inline; filename={}.csv'.format(
            normalize_for_url(
                '{}-{}'.format(
                    self.title,
                    request.translate(_("Parties")).lower()
                )
            )
        )
    )
