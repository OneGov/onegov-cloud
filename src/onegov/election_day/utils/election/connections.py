from __future__ import annotations

from collections import OrderedDict
from itertools import groupby
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import groupbylist, module_path
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ProporzElection
from onegov.election_day.utils.common import LastUpdatedOrderedDict
from onegov.election_day.utils.common import sublist_name_from_connection_id
from operator import attrgetter
from sqlalchemy import select

from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSONObject
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.models import Election
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import TypeAlias
    from uuid import UUID

    Sublist: TypeAlias = tuple[str, int, str]
    Subconnection: TypeAlias = tuple[str, int, list[Sublist]]
    Connection: TypeAlias = tuple[str, int, list[Sublist], list[Subconnection]]


def to_int(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def get_connection_results_api(
    election: Election,
    session: Session
) -> JSONObject_ro:

    connection_query = as_selectable_from_path(
        module_path(
            'onegov.election_day', 'queries/connection_results.sql'
        )
    )
    conn_query = connection_query.c
    query = select(conn_query).where(conn_query.election_id == election.id)
    results = session.execute(query)

    data: dict[str, Any] = LastUpdatedOrderedDict({})

    for conn, g in groupby(results, attrgetter('conn')):
        for lst in g:
            data.setdefault(conn, LastUpdatedOrderedDict())
            data[conn].setdefault('total_votes', int(lst.conn_votes))
            if not lst.subconn:
                conn_lists = data[conn].setdefault(
                    'lists', LastUpdatedOrderedDict()
                )
                conn_lists.setdefault(lst.list_name, int(lst.list_votes))
            else:
                subconns = data[conn].setdefault(
                    'subconns', LastUpdatedOrderedDict()
                )

                subconn_display = sublist_name_from_connection_id(
                    lst.subconn, lst.conn
                )
                subconn = subconns.setdefault(
                    subconn_display, LastUpdatedOrderedDict()
                )
                subconn.setdefault('total_votes', int(lst.subconn_votes))

                lists = subconn.setdefault('lists', LastUpdatedOrderedDict())
                lists.setdefault(lst.list_name, int(lst.list_votes))
    return data


def get_connection_results(
    election: Election,
    session: Session
) -> list[Connection]:
    """ Returns the aggregated list connection results as list. """

    if election.type != 'proporz':
        return []

    parents: Query[tuple[UUID, str, int]] = session.query(
        ListConnection.id,
        ListConnection.connection_id,
        ListConnection.votes
    )
    parents = parents.filter(
        ListConnection.election_id == election.id,
        ListConnection.parent_id.is_(None)
    )
    parents = parents.order_by(ListConnection.connection_id)

    children_query: Query[tuple[UUID | None, str, int, UUID]]
    children_query = session.query(
        ListConnection.parent_id,
        ListConnection.connection_id,
        ListConnection.votes,
        ListConnection.id
    )
    children_query = children_query.filter(
        ListConnection.election_id == election.id,
        ListConnection.parent_id.isnot(None)
    )
    children_query = children_query.order_by(
        ListConnection.parent_id,
        ListConnection.connection_id
    )
    children = dict(groupbylist(children_query, lambda x: str(x[0])))

    sublists_query: Query[tuple[UUID, str, int, str]] = session.query(
        List.connection_id,
        List.name,
        List.votes,
        List.list_id
    )
    sublists_query = sublists_query.filter(
        List.connection_id.isnot(None),
        List.election_id == election.id
    )
    sublists_query = sublists_query.order_by(List.connection_id)
    sublists = dict(groupbylist(sublists_query, lambda x: str(x[0])))

    result = []
    for parent in parents:
        connection_id = str(parent[0])
        subconnections: list[Subconnection] = [(
            child[1],
            int(child[2]),
            [(l[1], l[2], l[3]) for l in sorted(
                sublists.get(str(child[3]), []),
                key=lambda x: to_int(x[3])
            )]
        ) for child in children.get(connection_id, [])]

        subconnection_votes = sum(c[1] for c in subconnections)
        connection: Connection = (
            parent[1],
            int(parent[2] + subconnection_votes),
            [(l[1], l[2], l[3]) for l in sublists.get(connection_id, [])],
            subconnections
        )
        result.append(connection)

    return result


def get_connections_data(
    election: Election,
) -> JSONObject_ro:
    """" View the list connections as JSON. Used to for the connection sankey
    chart. """

    if not isinstance(election, ProporzElection):
        return {}

    nodes: dict[UUID, JSONObject] = OrderedDict()
    links: list[JSONObject_ro] = []
    completed = election.completed

    # Add lists
    for list_ in election.lists:
        nodes[list_.id] = {
            'name': list_.name,
            'value': list_.votes,
            'display_value': list_.number_of_mandates or '' if
            completed else '',
            'active': list_.number_of_mandates > 0 and completed
        }
        if list_.connection:
            mandates = list_.connection.total_number_of_mandates
            nodes.setdefault(list_.connection.id, {
                'name': '',
                'display_value': mandates or '' if completed else '',
                'active': mandates > 0 and completed
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
                'display_value': mandates or '' if completed else '',
                'active': mandates > 0 and completed
            })
            mandates = connection.parent.total_number_of_mandates
            nodes.setdefault(connection.parent.id, {
                'name': '',
                'display_value': mandates or '' if completed else '',
                'active': mandates > 0 and completed
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
