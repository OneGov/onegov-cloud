from onegov.ballot import (
    Candidate,
    CandidateResult,
    ElectionResult,
    List,
    ListConnection
)
from onegov.core.utils import groupbylist
from sqlalchemy import desc


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

    # guess the grouping
    tester = session.query(ElectionResult.group)
    tester = tester.filter(ElectionResult.election_id == election.id)
    tester = tester.first()

    for id_ in set(all_.keys()) - set(used):
        group = all_[id_]['name']
        if tester and '/' in tester[0]:
            group = '/'.join(
                p for p in (
                    all_[id_].get('district'),
                    all_[id_].get('name')
                ) if p is not None
            )

        result.append(group)

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
