from morepath.request import Response
from onegov.ballot import ElectionCompound
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.custom import json
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.html(
    model=ElectionCompound,
    name='data',
    template='election_compound/data.pt',
    permission=Public
)
def view_election_compound_data(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'data')

    return {
        'election_compound': self,
        'layout': layout
    }


@ElectionDayApp.view(
    model=ElectionCompound,
    name='data-json',
    permission=Public
)
def view_election_compound_data_as_json(self, request):

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
    model=ElectionCompound,
    name='data-csv',
    permission=Public
)
def view_election_compound_data_as_csv(self, request):

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
    model=ElectionCompound,
    name='data-parties',
    permission=Public
)
def view_election_compound_parties_data_as_csv(self, request):

    """ View the raw parties data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return Response(
        convert_list_of_dicts_to_csv(self.export_parties()),
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
