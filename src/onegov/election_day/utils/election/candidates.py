from __future__ import annotations

from onegov.core.utils import groupbylist
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from operator import itemgetter
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import object_session
from sqlalchemy.sql.expression import case
from sqlalchemy.sql.expression import literal_column


from typing import cast
from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.types import JSONObject_ro
    from onegov.election_day.models import Election
    from onegov.election_day.models import ProporzElection
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from sqlalchemy.sql.elements import Label
    from typing import NamedTuple
    from uuid import UUID

    class CandidateResultRow(NamedTuple):
        votes: int
        family_name: str
        first_name: str
        elected: bool
        party: str | None
        percentage: float
        list_name: str | None
        list_id: str | None

    class CandidateRow(NamedTuple):
        id: UUID
        family_name: str
        first_name: str
        votes: int

    class ResultRow(NamedTuple):
        name: str
        family_name: str
        first_name: str
        votes: int


def get_candidates_results(
    election: Election,
    session: Session,
    entities: Collection[str] | None = None,
) -> Query[CandidateResultRow]:
    """ Returns the aggregated candidates results as list.

    Also includes percentages of votes for majorz elections. Be aware that this
    may contain rounding errors.
    """
    election_result_ids = []
    if entities:
        election_result_ids_q = session.query(ElectionResult.id).filter(
            ElectionResult.election_id == election.id,
            ElectionResult.name.in_(entities)
        )
        election_result_ids = [result for result, in election_result_ids_q]

    percentage: Label[Any] = literal_column('0').label('percentage')
    if election.type == 'majorz':
        accounted = session.query(func.sum(ElectionResult.accounted_ballots))
        accounted = accounted.filter(ElectionResult.election_id == election.id)
        if entities:
            accounted = accounted.filter(
                ElectionResult.id.in_(election_result_ids)
            )
        num_accounted = accounted.scalar() or 1
        percentage = func.round(
            100 * func.sum(CandidateResult.votes) / float(num_accounted), 1
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
    election: Election,
    limit: int | None = None,
    lists: Collection[str] | None = None,
    elected: bool | None = None,
    sort_by_lists: bool = False,
    entities: Collection[str] | None = None
) -> JSONObject_ro:
    """" Get the candidates as JSON. Used to for the candidates bar chart.

    Allows to optionally

    * return only the first ``limit`` results.
    * return only results for candidates within the given list names (proporz)
      or party names (majorz).
    * return only elected candidates. If not specified, only elected candidates
      are returned for proporz elections, all for majorz elections.

    """

    elected = election.type == 'proporz' if elected is None else elected

    session = object_session(election)

    colors = election.colors
    column = Candidate.party
    if election.type == 'proporz':
        election = cast('ProporzElection', election)
        column = Candidate.list_id  # type:ignore[assignment]
        names = {list_.name: str(list_.id) for list_ in election.lists}
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
        order.insert(0, case(  # type: ignore[call-overload]
            *(
                (column == name, index)
                for index, name in enumerate(lists, 1)
            ),
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
                    'active'
                    if candidate.elected or not election.allocated_mandates
                    else 'inactive'
                ),
                'color': (
                    colors.get(candidate.party)
                    or colors.get(str(candidate.list_id))
                )
            } for candidate in candidates
        ],
        'majority': majority,
        'title': election.title
    }


def get_candidates_results_by_entity(
    election: Election,
    sort_by_votes: bool = False
) -> tuple[list[CandidateRow], list[tuple[str, list[ResultRow]]]]:
    """ Returns the candidates results by entity.

    Allows to optionally order by the number of total votes instead of the
    candidate names.

    """

    session = object_session(election)

    query = session.query(
        Candidate.id,
        Candidate.family_name,
        Candidate.first_name,
        Candidate.votes.label('votes')
    )
    if sort_by_votes:
        query = query.order_by(
            Candidate.votes.desc(),
            Candidate.family_name,
            Candidate.first_name
        )
    else:
        query = query.order_by(
            Candidate.family_name,
            Candidate.first_name
        )
    query = query.filter(Candidate.election_id == election.id)
    candidates = query.all()

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

    return candidates, groupbylist(results, key=itemgetter(0))
