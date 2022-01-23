from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_list_groups_data


@ElectionDayApp.json(
    model=ElectionCompound,
    name='list-groups-data',
    permission=Public
)
def view_election_compound_list_groups_data(self, request):

    """" View the list groups as JSON. Used to for the lists bar chart. """

    return get_list_groups_data(self)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups-chart',
    template='embed.pt',
    permission=Public
)
def view_election_compound_list_groups_chart(self, request):

    """" View the list groups as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request),
        'type': 'list-groups-chart',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_list_groups_table(self, request):

    """" View the list groups as table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'groups': get_list_groups(self),
        'layout': ElectionCompoundLayout(self, request),
        'type': 'election-compound-table',
        'scope': 'list-groups',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='list-groups',
    template='election_compound/list_groups.pt',
    permission=Public
)
def view_election_compound_list_groups(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'list-groups')

    return {
        'election_compound': self,
        'layout': layout,
        'groups': get_list_groups(self),
    }


@ElectionDayApp.svg_file(model=ElectionCompound, name='list-groups-svg')
def view_election_compound_list_groups_svg(self, request):

    """ View the list groups as SVG. """

    layout = ElectionCompoundLayout(self, request, 'list-groups')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
