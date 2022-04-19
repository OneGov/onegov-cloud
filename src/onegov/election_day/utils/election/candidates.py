from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.core.utils import groupbylist
from sqlalchemy import desc
from sqlalchemy.orm import object_session
from sqlalchemy.sql.expression import case


def get_candidates_results(election, session):
    """ Returns the aggregated candidates results as list. """

    result = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.party,
        Candidate.votes.label('votes'),
        List.name,
        List.list_id
    )
    result = result.outerjoin(List)
    result = result.filter(Candidate.election_id == election.id)

    if election.completed:
        result = result.order_by(
            List.list_id,
            desc(Candidate.elected),
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        result = result.order_by(
            List.list_id,
            desc(Candidate.votes),
            Candidate.family_name,
            Candidate.first_name
        )

    return result


def get_candidates_data(
    election, limit=None, lists=None, elected=None, sort_by_lists=None
):
    """" Get the candidates as JSON. Used to for the candidates bar chart.

    Allows to optionally
    - return only the first ``limit`` results.
    - return only results for candidates within the given list names (proporz)
      or party names (majorz).
    - return only elected candidates. If not specified, only elected candidates
      are returned for proporz elections, all for majorz elections.

    """

    elected = election.type == 'proporz' if elected is None else elected

    session = object_session(election)

    colors = election.colors
    default_color = '#999' if election.colors else ''
    column = Candidate.party
    if election.type == 'proporz':
        column = Candidate.list_id
        names = dict(election.lists.with_entities(List.name, List.id))
        colors = {
            list_id: election.colors[name]
            for name, list_id in names.items()
            if name in election.colors
        }
        if lists:
            lists = [names.get(l, '') for l in lists if l in names]

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.votes.label('votes'),
        Candidate.list_id,
        Candidate.party
    )
    candidates = candidates.filter(Candidate.election_id == election.id)
    if lists:
        candidates = candidates.filter(column.in_(lists))
    if elected:
        candidates = candidates.filter(Candidate.elected == True)

    order = [
        desc(Candidate.votes),
        Candidate.family_name,
        Candidate.first_name
    ]
    if election.completed:
        order.insert(0, desc(Candidate.elected))
    if lists and sort_by_lists:
        order.insert(0, case(
            [
                (column == name, index)
                for index, name in enumerate(lists, 1)
            ],
            else_=0
        ))
    candidates = candidates.order_by(*order)

    if limit and limit > 0:
        candidates = candidates.limit(limit)

    majority = 0
    if (
        election.type == 'majorz'
        and election.majority_type == 'absolute'
        and election.absolute_majority is not None
        and election.completed
    ):
        majority = election.absolute_majority

    return {
        'results': [
            {
                'text': '{} {}'.format(
                    candidate.family_name, candidate.first_name
                ),
                'value': candidate.votes,
                'class': (
                    'active' if candidate.elected and election.completed
                    else 'inactive'
                ),
                'color': (
                    colors.get(candidate.party)
                    or colors.get(candidate.list_id)
                    or default_color
                )
            } for candidate in candidates
        ],
        'majority': majority,
        'title': election.title
    }


def get_candidates_results_by_entity(election):
    """ Returns the candidates results by entity. """

    session = object_session(election)

    candidates = session.query(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.votes.label('votes')
    )
    candidates = candidates.order_by(
        Candidate.family_name,
        Candidate.first_name
    )
    candidates = candidates.filter(Candidate.election_id == election.id)

    results = session.query(
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name,
        CandidateResult.votes
    )
    results = results.outerjoin(Candidate, ElectionResult)
    results = results.filter(ElectionResult.election_id == election.id)
    results = results.filter(Candidate.election_id == election.id)
    results = results.order_by(
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name
    )

    return candidates.all(), groupbylist(results, key=lambda x: x[0])
