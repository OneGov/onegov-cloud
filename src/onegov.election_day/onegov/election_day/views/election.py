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
from sqlalchemy import desc
from sqlalchemy.orm import object_session


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_election(self, request):

    layout = DefaultLayout(self, request)
    request.include('bar_chart')

    majorz = self.type == 'majorz'
    session = object_session(self)

    # Candidates: Overview
    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes,
        List.name,
    )
    candidates = candidates.outerjoin(List)
    candidates = candidates.order_by(
        List.name,
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

    # List results
    lists = []
    if not majorz:
        lists = session.query(
            List.name,
            List.votes,
            List.number_of_mandates
        )
        lists = lists.order_by(
            desc(List.number_of_mandates),
            desc(List.votes),
            List.name
        )
        lists = lists.filter(List.election_id == self.id)

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
            List.votes
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
                [(l[1], l[2]) for l in sublists.get(str(child[3]), [])]
            ) for child in children.get(id, [])]
            connection = [
                parent[1],
                parent[2] or 0,
                [(list[1], list[2]) for list in sublists.get(id, [])],
                subconnections
            ]
            connection[1] += sum([c[1] for c in connection[3]])
            connections.append(connection)

    return {
        'election': self,
        'layout': layout,
        'majorz': majorz,
        'has_results': True if self.results.first() else False,
        'candidates': candidates,
        'electoral': electoral,
        'lists': lists,
        'connections': connections,
    }


@ElectionDayApp.json(model=Election, name='json', permission=Public)
def view_election_as_json(self, request):
    return self.export()


@ElectionDayApp.view(model=Election, name='csv', permission=Public)
def view_election_as_csv(self, request):
    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Election, name='xlsx', permission=Public)
def view_election_as_xlsx(self, request):
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

    return [{
        'text': '{} {}'.format(candidate[0], candidate[1]),
        'value': candidate[3],
        'class': 'active' if candidate[2] else 'inactive'
    } for candidate in candidates.all()]


@ElectionDayApp.json(model=Election, permission=Public, name='lists')
def view_election_lists(self, request):
    if self.type == 'majorz':
        return []

    session = object_session(self)

    lists = session.query(
        List.name,
        List.votes,
        List.number_of_mandates
    )
    lists = lists.order_by(
        desc(List.number_of_mandates),
        desc(List.votes),
        List.name
    )
    lists = lists.filter(List.election_id == self.id)

    return [{
        'text': list[0],
        'value': list[1],
        'secondary': list[2],
        'class': 'active' if list[2] > 0 else 'inactive'
    } for list in lists.all()]
