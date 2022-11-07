from onegov.ballot import ElectionCompound
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


@ElectionDayApp.json_file(model=ElectionCompound, name='data-json')
def view_election_compound_data_as_json(self, request):

    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export(sorted(request.app.locales)),
        'name': normalize_for_url(self.title)
    }


@ElectionDayApp.csv_file(model=ElectionCompound, name='data-csv')
def view_election_compound_data_as_csv(self, request):

    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    max_filename_len = 60
    filename = self.title[:max_filename_len]
    return {
        'data': self.export(sorted(request.app.locales)),
        'name': normalize_for_url(filename)
    }


@ElectionDayApp.json_file(model=ElectionCompound, name='data-parties-json')
def view_election_compound_parties_data_as_json(self, request):

    """ View the raw parties data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export_parties(
            locales=sorted(request.app.locales),
            default_locale=request.app.default_locale,
            json_serializable=True
        ),
        'name': '{}-{}'.format(
            self.title,
            request.translate(_("Parties")).lower()
        )
    }


@ElectionDayApp.csv_file(model=ElectionCompound, name='data-parties-csv')
def view_election_compound_parties_data_as_csv(self, request):

    """ View the raw parties data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'data': self.export_parties(
            locales=sorted(request.app.locales),
            default_locale=request.app.default_locale
        ),
        'name': '{}-{}'.format(
            self.title,
            request.translate(_("Parties")).lower()
        )
    }
