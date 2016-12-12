from collections import OrderedDict
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout, ElectionsLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import handle_headerless_params
from onegov.election_day.views.election import get_connection_results
from sqlalchemy.orm import object_session


@ElectionDayApp.json(model=Election, permission=Public,
                     name='connections-data')
def view_election_connections_data(self, request):
    """" View the list connections as JSON. Used to for the connection sankey
    chart. """

    if self.type == 'majorz':
        return {}

    nodes = OrderedDict()
    links = []

    # Add lists
    for list_ in self.lists:
        nodes[list_.id] = {
            'name': list_.name,
            'value': list_.votes,
            'display_value': list_.number_of_mandates or '',
            'active': list_.number_of_mandates > 0
        }
        if list_.connection:
            mandates = list_.connection.total_number_of_mandates
            nodes.setdefault(list_.connection.id, {
                'name': '',
                'display_value': mandates or '',
                'active': mandates > 0
            })
            links.append({
                'source': list(nodes.keys()).index(list_.id),
                'target': list(nodes.keys()).index(list_.connection.id),
                'value': list_.votes
            })

    # Add remaining connections
    for connection in self.list_connections:
        if connection.parent:
            mandates = connection.total_number_of_mandates
            nodes.setdefault(connection.id, {
                'name': '',
                'display_value': mandates or '',
                'active': mandates > 0
            })
            mandates = connection.parent.total_number_of_mandates
            nodes.setdefault(connection.parent.id, {
                'name': '',
                'display_value': mandates or '',
                'active': mandates > 0
            })
            links.append({
                'source': list(nodes.keys()).index(connection.id),
                'target': list(nodes.keys()).index(connection.parent.id),
                'value': connection.votes
            })

    count = 0
    for key in nodes.keys():
        count = count + 1
        nodes[key]['id'] = count

    return {
        'nodes': list(nodes.values()),
        'links': links,
        'title': self.title
    }


@ElectionDayApp.html(model=Election, permission=Public,
                     name='connections-chart', template='embed.pt')
def view_election_connections_chart(self, request):
    """" View the connections as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('sankey_chart')
    request.include('frame_resizer')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'sankey': request.link(self, name='connections-data'),
            'inverse': 'true'
        }
    }


@ElectionDayApp.html(model=Election, template='election/connections.pt',
                     name='connections', permission=Public)
def view_election_connections(self, request):
    """" The main view. """

    request.include('sankey_chart')
    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'connections'),
        'connections': get_connection_results(self, object_session(self)),
    }
