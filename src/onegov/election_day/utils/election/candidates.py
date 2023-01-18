from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.core.utils import groupbylist
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import object_session
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import literal_column


def get_candidates_results(election, session, entities=None):
    """ Returns the aggregated candidates results as list.

    Also includes percentages of votes for majorz elections. Be aware that this
    may contain rounding errors.
    """
    election_result_ids = []
    if entities:
        election_result_ids = session.query(ElectionResult.id).filter(
            ElectionResult.election_id == election.id,
            ElectionResult.name.in_(entities)
        )
        election_result_ids = [result.id for result in election_result_ids]

    percentage = literal_column('0').label('percentage')
    if election.type == 'majorz':
        accounted = session.query(func.sum(ElectionResult.accounted_ballots))
        accounted = accounted.filter(ElectionResult.election_id == election.id)
        if entities:
            accounted = accounted.filter(
                ElectionResult.id.in_(election_result_ids)
            )
        accounted = accounted.scalar() or 1
        percentage = func.round(
            100 * func.sum(CandidateResult.votes) / float(accounted), 1
        ).label('percentage')

    result = session.query(
        func.sum(CandidateResult.votes).label('votes'),
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.party,
        percentage,
        List.name.label('list_name'),
        List.list_id.label('list_id')
    )
    result = result.join(CandidateResult.candidate)
    result = result.join(Candidate.list, isouter=True)
    result = result.filter(Candidate.election_id == election.id)
    if entities:
        result = result.filter(
            CandidateResult.election_result_id.in_(election_result_ids)
        )
    result = result.group_by(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.party,
        List.name.label('list_name'),
        List.list_id.label('list_id')
    )

    if election.completed:
        result = result.order_by(
            List.list_id,
            desc(Candidate.elected),
            desc('votes'),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        result = result.order_by(
            List.list_id,
            desc('votes'),
            Candidate.family_name,
            Candidate.first_name
        )

    return result


def get_candidates_data(
    election, limit=None, lists=None, elected=None, sort_by_lists=None,
    entities=None
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
        func.sum(CandidateResult.votes).label('votes'),
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.list_id,
        Candidate.party
    )
    candidates = candidates.join(CandidateResult.candidate)
    candidates = candidates.filter(Candidate.election_id == election.id)
    if lists:
        candidates = candidates.filter(column.in_(lists))
    if elected:
        candidates = candidates.filter(Candidate.elected == True)
    if entities:
        election_result_id = session.query(ElectionResult.id).filter(
            ElectionResult.election_id == election.id,
            ElectionResult.name.in_(entities)
        )
        election_result_id = [result.id for result in election_result_id]
        candidates = candidates.filter(
            CandidateResult.election_result_id.in_(election_result_id)
        )
    candidates = candidates.group_by(
        Candidate.family_name,
        Candidate.first_name,
        Candidate.elected,
        Candidate.list_id,
        Candidate.party
    )
    order = [
        desc('votes'),
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
        and not entities
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
                )
            } for candidate in candidates
        ],
        'majority': majority,
        'title': election.title
    }


def get_candidates_results_by_entity(election, sort_by_votes=False):
    """ Returns the candidates results by entity.

    Allows to optionally order by the number of total votes instead of the
    candidate names.

    """

    session = object_session(election)

    candidates = session.query(
        Candidate.id,
        Candidate.family_name,
        Candidate.first_name,
        Candidate.votes.label('votes')
    )
    if sort_by_votes:
        candidates = candidates.order_by(
            Candidate.votes.desc(),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        candidates = candidates.order_by(
            Candidate.family_name,
            Candidate.first_name
        )
    candidates = candidates.filter(Candidate.election_id == election.id)
    candidates = candidates.all()

    results = session.query(
        ElectionResult.name,
        Candidate.family_name,
        Candidate.first_name,
        CandidateResult.votes
    )
    results = results.outerjoin(Candidate, ElectionResult)
    results = results.filter(ElectionResult.election_id == election.id)
    results = results.filter(Candidate.election_id == election.id)
    if candidates:
        results = results.order_by(
            ElectionResult.name,
            case(
                [
                    (Candidate.id == candidate.id, index)
                    for index, candidate in enumerate(candidates, 1)
                ],
                else_=0
            )
        )

    return candidates, groupbylist(results, key=lambda x: x[0])
