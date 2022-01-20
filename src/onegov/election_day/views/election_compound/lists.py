from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout, ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_parameter
from onegov.election_day.utils.election_compound import get_list_results
from onegov.election_day.utils.election_compound import get_lists_data


@ElectionDayApp.json(
    model=ElectionCompound,
    name='lists-data',
    permission=Public
)
def view_election_compound_lists_data(self, request):

    """" View the lists as JSON. Used to for the lists bar chart. """

    limit = get_parameter(request, 'limit', int, None)
    names = get_parameter(request, 'names', list, None)

    return get_lists_data(
        self, limit=limit, names=names,
        mandates_only=self.after_pukelsheim
    )


@ElectionDayApp.html(
    model=ElectionCompound,
    name='lists-chart',
    template='embed.pt',
    permission=Public
)
def view_election_compound_lists_chart(self, request):

    """" View the lists as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'lists-chart',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='lists-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_lists_table(self, request):

    """" View the lists as table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'lists': get_list_results(self),
        'layout': DefaultLayout(self, request),
        'type': 'election-compound-table',
        'scope': 'lists',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='lists',
    template='election_compound/lists.pt',
    permission=Public
)
def view_election_compound_lists(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'lists')

    return {
        'election_compound': self,
        'layout': layout,
        'lists': get_list_results(self),
    }


@ElectionDayApp.svg_file(model=ElectionCompound, name='lists-svg')
def view_election_compound_lists_svg(self, request):

    """ View the lists as SVG. """

    layout = ElectionCompoundLayout(self, request, 'lists')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
