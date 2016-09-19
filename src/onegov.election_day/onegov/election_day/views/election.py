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
from onegov.election_day.utils import get_election_summary
from sqlalchemy import desc
from sqlalchemy.orm import object_session


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return value


def get_missing_entities(election, request, session):
    result = []

    all_ = request.app.principal.entities[election.date.year]

    used = session.query(ElectionResult.entity_id)
    used = used.filter(ElectionResult.election_id == election.id)
    used = used.distinct()
    used = [item[0] for item in used]

    for id in set(all_.keys()) - set(used):
        result.append(all_[id]['name'])

    return result


def get_candidates_results(election, session):
    """ Returns the aggregated candidates results as list. """

    result = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes,
        List.name,
        List.list_id
    )
    result = result.outerjoin(List)
    result = result.order_by(
        List.list_id,
        desc(Candidate.elected),
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    )
    result = result.filter(Candidate.election_id == election.id)

    return result


def get_candidate_electoral_results(election, session):
    """ Returns the aggregated candidates results per entity as list. """

    if election.type != 'majorz':
        return []

    result = session.query(ElectionResult.group, CandidateResult.votes)
    result = result.outerjoin(CandidateResult, Candidate)
    result = result.order_by(
        ElectionResult.group,
        Candidate.candidate_id
    )
    result = result.filter(ElectionResult.election_id == election.id)
    result = groupbylist(result, lambda x: x[0])

    return result


def get_list_results(election, session):
    """ Returns the aggregated list results as list. """

    result = session.query(List.name, List.votes, List.list_id)
    result = result.order_by(desc(List.votes))
    result = result.filter(List.election_id == election.id)

    return result


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
        ListConnection.election_id == election.id,
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


@ElectionDayApp.html(model=Election, template='election.pt', permission=Public)
def view_election(self, request):
    """" The main view. """

    request.include('bar_chart')
    request.include('sankey_chart')

    session = object_session(self)

    candidates = get_candidates_results(self, session).all()

    return {
        'election': self,
        'layout': DefaultLayout(self, request),
        'majorz': self.type == 'majorz',
        'has_results': True if self.results.first() else False,
        'candidates': candidates,
        'number_of_candidates': len(candidates),
        'electoral': get_candidate_electoral_results(self, session),
        'connections': get_connection_results(self, session),
        'missing_entities': get_missing_entities(
            self, request, session
        ),
    }


@ElectionDayApp.json(model=Election, permission=Public, name='candidates')
def view_election_candidates(self, request):
    """" View the candidates as JSON. Used to for the candidates bar chart. """

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


@ElectionDayApp.html(model=Election, permission=Public,
                     name='candidates-chart', template='embed.pt')
def view_election_candidates_chart(self, request):
    """" View the candidates as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('bar_chart')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'bar': request.link(self, name='candidates')
        }
    }


@ElectionDayApp.json(model=Election, permission=Public, name='lists')
def view_election_lists(self, request):
    """" View the lists as JSON. Used to for the lists bar chart. """

    if self.type == 'majorz':
        return {
            'results': [],
            'majority': None,
            'title': self.title
        }

    return {
        'results': [{
            'text': item[0],
            'value': item[1],
            'class': 'inactive'
        } for item in get_list_results(self, object_session(self))],
        'majority': None,
        'title': self.title
    }


@ElectionDayApp.html(model=Election, permission=Public,
                     name='lists-chart', template='embed.pt')
def view_election_lists_chart(self, request):
    """" View the lists as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('bar_chart')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'bar': request.link(self, name='lists')
        }
    }


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

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'sankey': request.link(self, name='connections')
        }
    }


@ElectionDayApp.json(model=Election, permission=Public, name='json')
def view_election_json(self, request):
    """" The main view as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    data = {
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': self.last_result_change.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.counted_entities or 0,
            'total': self.total_entities or 0,
        },
        'related_link': (self.meta or {}).get('related_link', ''),
        'title': self.title_translations,
        'type': 'election',
        'statistics': {
            'total': {
                'elegible_voters': self.elegible_voters,
                'received_ballots': self.received_ballots,
                'accounted_ballots': self.accounted_ballots,
                'blank_ballots': self.blank_ballots,
                'invalid_ballots': self.invalid_ballots,
                'accounted_votes': self.accounted_votes,
                'turnout': self.turnout,
            },
            'districts': [
                {
                    'elegible_voters': district.elegible_voters,
                    'received_ballots': district.received_ballots,
                    'accounted_ballots': district.accounted_ballots,
                    'blank_ballots': district.blank_ballots,
                    'invalid_ballots': district.invalid_ballots,
                    'accounted_votes': district.accounted_votes,
                    'turnout': district.turnout,
                    'name': district.group,
                    'id': district.entity_id,
                } for district in self.results
            ],
        },
        'election_type': self.type,
        'url': request.link(self),
        'embed': [
            request.link(self, 'lists-chart'),
            request.link(self, 'connections-chart'),
        ] if self.type == 'proporz' else [
            request.link(self, 'candidates-chart'),
        ]
    }

    session = object_session(self)

    if self.type == 'majorz':
        data['absolute_majority'] = self.absolute_majority
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'votes': candidate[3],
            } for candidate in get_candidates_results(self, session)
        ]

    if self.type == 'proporz':
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'votes': candidate[3],
                'list_name': candidate[4],
                'list_list_id': candidate[5]
            } for candidate in get_candidates_results(self, session)
        ]

        data['lists'] = [
            {
                'name': item[0],
                'votes': item[1],
                'id': item[2],
            } for item in get_list_results(self, session)
        ]

        data['list_connections'] = [
            {
                'id': connection[0],
                'votes': connection[1],
                'lists': [
                    {
                        'name': item[0],
                        'votes': item[1],
                        'id': item[2],
                    } for item in connection[2]
                ],
                'subconnections': [
                    {
                        'id': subconnection[0],
                        'votes': subconnection[1],
                        'lists': [
                            {
                                'name': item[0],
                                'votes': item[1],
                                'id': item[2],
                            } for item in subconnection[2]
                        ],
                    } for subconnection in connection[3]
                ],
            } for connection in get_connection_results(self, session)
        ]

    return data


@ElectionDayApp.json(model=Election, permission=Public, name='summary')
def view_election_summary(self, request):
    """ View the summary of the election as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_election_summary(self, request)


@ElectionDayApp.json(model=Election, name='data-json', permission=Public)
def view_election_data_as_json(self, request):
    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return self.export()


@ElectionDayApp.view(model=Election, name='data-csv', permission=Public)
def view_election_data_as_csv(self, request):
    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Election, name='data-xlsx', permission=Public)
def view_election_data_as_xlsx(self, request):
    """ View the raw data as XLSX. """

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
