from collections import OrderedDict
from morepath.request import Response
from onegov.ballot import (
    Candidate,
    CandidateResult,
    Election,
    ElectionResult,
    List,
    ListConnection
)
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import desc
from sqlalchemy.orm import object_session


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return value


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_election(self, request):

    layout = DefaultLayout(self, request)
    request.include('bar_chart')
    request.include('sankey_chart')

    majorz = self.type == 'majorz'
    session = object_session(self)

    # Candidates: Overview
    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes,
        List.name,
        List.list_id
    )
    candidates = candidates.outerjoin(List)
    candidates = candidates.order_by(
        List.list_id,
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == self.id)

    # Candidates: Electoral results
    electoral = []
    if majorz:
        electoral = session.query(ElectionResult.group, CandidateResult.votes)
        electoral = electoral.outerjoin(CandidateResult, Candidate)
        electoral = electoral.order_by(
            ElectionResult.group,
            Candidate.candidate_id
        )
        electoral = electoral.filter(ElectionResult.election_id == self.id)
        electoral = groupbylist(electoral, lambda x: x[0])

    # List connections
    connections = []
    if not majorz:
        parents = session.query(
            ListConnection.id,
            ListConnection.connection_id,
            ListConnection.votes
        )
        parents = parents.filter(
            ListConnection.election_id == self.id,
            ListConnection.parent_id == None
        )
        parents = parents.order_by(ListConnection.connection_id)

        children = session.query(
            ListConnection.parent_id,
            ListConnection.connection_id,
            ListConnection.votes,
            ListConnection.id
        )
        children = children.filter(
            ListConnection.election_id == self.id,
            ListConnection.parent_id != None
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
            List.connection_id != None,
            List.election_id == self.id
        )
        sublists = sublists.order_by(List.connection_id)
        sublists = dict(groupbylist(sublists, lambda x: str(x[0])))

        for parent in parents:
            id = str(parent[0])
            subconnections = [(
                child[1],
                child[2],
                [(l[1], l[2]) for l in sorted(
                    sublists.get(str(child[3]), []),
                    key=lambda x: to_int(x[3])
                )]
            ) for child in children.get(id, [])]

            connection = [
                parent[1],
                parent[2] or 0,
                [(list[1], list[2]) for list in sublists.get(id, [])],
                subconnections
            ]
            connection[1] += sum([c[1] for c in connection[3]])
            connections.append(connection)

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return {
        'election': self,
        'layout': layout,
        'majorz': majorz,
        'has_results': True if self.results.first() else False,
        'candidates': candidates,
        'electoral': electoral,
        'connections': connections,
    }


@ElectionDayApp.json(model=Election, name='json', permission=Public)
def view_election_as_json(self, request):

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return self.export()


@ElectionDayApp.view(model=Election, name='csv', permission=Public)
def view_election_as_csv(self, request):

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Election, name='xlsx', permission=Public)
def view_election_as_xlsx(self, request):

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


@ElectionDayApp.json(model=Election, permission=Public, name='candidates')
def view_election_candidates(self, request):
    session = object_session(self)

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes
    )
    candidates = candidates.order_by(
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == self.id)

    majority = 0
    if self.type == 'majorz' and self.absolute_majority is not None:
        majority = self.absolute_majority

    return {
        'results': [{
            'text': '{} {}'.format(candidate[0], candidate[1]),
            'value': candidate[3],
            'class': 'active' if candidate[2] else 'inactive'
        } for candidate in candidates.all()],
        'majority': majority,
        'title': self.title
    }


@ElectionDayApp.json(model=Election, permission=Public, name='lists')
def view_election_lists(self, request):
    if self.type == 'majorz':
        return {}

    session = object_session(self)

    lists = session.query(List.name, List.votes)
    lists = lists.order_by(desc(List.votes))
    lists = lists.filter(List.election_id == self.id)

    return {
        'results': [{
            'text': list[0],
            'value': list[1],
            'class': 'inactive'
        } for list in lists.all()],
        'majority': None,
        'title': self.title
    }


@ElectionDayApp.json(model=Election, permission=Public, name='connections')
def view_election_connections(self, request):
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
