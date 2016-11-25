from collections import OrderedDict
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.json(model=Election, permission=Public, name='connections')
def view_election_connections(self, request):
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
            'value_2': list_.number_of_mandates,
        }
        if list_.connection:
            nodes.setdefault(list_.connection.id, {
                'name': '',
                'value_2': list_.connection.total_number_of_mandates,
            })
            links.append({
                'source': list(nodes.keys()).index(list_.id),
                'target': list(nodes.keys()).index(list_.connection.id),
                'value': list_.votes
            })

    # Add remaining connections
    for connection in self.list_connections:
        if connection.parent:
            nodes.setdefault(connection.id, {
                'name': '',
                'value_2': connection.total_number_of_mandates,
            })
            nodes.setdefault(connection.parent.id, {
                'name': '',
                'value_2': connection.parent.total_number_of_mandates,
            })
            links.append({
                'source': list(nodes.keys()).index(connection.id),
                'target': list(nodes.keys()).index(connection.parent.id),
                'value': connection.votes
            })

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
            'sankey': request.link(self, name='connections')
        }
    }
