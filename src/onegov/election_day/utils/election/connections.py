from collections import OrderedDict
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.core.utils import groupbylist


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return value


def get_connection_results(election, session):
    """ Returns the aggregated list connection results as list. """

    if election.type != 'proporz':
        return []

    parents = session.query(
        ListConnection.id,
        ListConnection.connection_id,
        ListConnection.votes
    )
    parents = parents.filter(
        ListConnection.election_id == election.id,
        ListConnection.parent_id.is_(None)
    )
    parents = parents.order_by(ListConnection.connection_id)

    children = session.query(
        ListConnection.parent_id,
        ListConnection.connection_id,
        ListConnection.votes,
        ListConnection.id
    )
    children = children.filter(
        ListConnection.election_id == election.id,
        ListConnection.parent_id.isnot(None)
    )
    children = children.order_by(
        ListConnection.parent_id,
        ListConnection.connection_id
    )
    children = dict(groupbylist(children, lambda x: str(x[0])))

    sublists = session.query(
        List.connection_id,
        List.name,
        List.votes,
        List.list_id
    )
    sublists = sublists.filter(
        List.connection_id.isnot(None),
        List.election_id == election.id
    )
    sublists = sublists.order_by(List.connection_id)
    sublists = dict(groupbylist(sublists, lambda x: str(x[0])))

    result = []
    for parent in parents:
        id = str(parent[0])
        subconnections = [(
            child[1],
            to_int(child[2]),
            [(l[1], l[2], l[3]) for l in sorted(
                sublists.get(str(child[3]), []),
                key=lambda x: to_int(x[3])
            )]
        ) for child in children.get(id, [])]

        connection = [
            parent[1],
            to_int(parent[2] or 0),
            [(list[1], list[2], list[3]) for list in sublists.get(id, [])],
            subconnections
        ]
        connection[1] += sum([c[1] for c in connection[3]])
        result.append(connection)

    return result


def get_connections_data(election, request):
    """" View the list connections as JSON. Used to for the connection sankey
    chart. """

    if election.type == 'majorz':
        return {}

    nodes = OrderedDict()
    links = []

    # Add lists
    for list_ in election.lists:
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
    for connection in election.list_connections:
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
        'title': election.title
    }
