from __future__ import annotations

from onegov.core.utils import groupbylist
from onegov.election_day.models import Candidate
from onegov.election_day.models import Election
from onegov.election_day.models import List
from operator import itemgetter
from sqlalchemy.orm import object_session
from statistics import mean


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import ElectionCompoundPart
    from onegov.election_day.types import Gender
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from typing import NamedTuple
    from typing import TypedDict

    class ElectedCandidateRow(NamedTuple):
        family_name: str
        first_name: str
        party: str | None
        gender: Gender | None
        year_of_birth: int | None
        list: str | None
        list_id: str | None
        election_id: str | None

    class CandidateStatistics(TypedDict):
        count: int
        age: int | None


def get_elected_candidates(
    election_compound: ElectionCompound | ElectionCompoundPart,
    session: Session
) -> Query[ElectedCandidateRow]:
    """ Returns the elected candidates of an election compound. """

    election_ids = [election.id for election in election_compound.elections]

    elected: Query[ElectedCandidateRow] = session.query(  # type: ignore[assignment]
        Candidate.family_name,
        Candidate.first_name,
        Candidate.party,
        Candidate.gender,
        Candidate.year_of_birth,
        List.name.label('list'),
        List.list_id,
        Election.id.label('election_id')
    )
    elected = elected.outerjoin(List, Candidate.list_id == List.id)
    elected = elected.outerjoin(Election)
    elected = elected.order_by(
        Election.shortcode,
        List.list_id,
        Candidate.family_name,
        Candidate.first_name
    )
    elected = elected.filter(Candidate.election_id.in_(election_ids))
    elected = elected.filter(Candidate.elected.is_(True))

    return elected


def get_candidate_statistics(
    election_compound: ElectionCompound | ElectionCompoundPart,
    elected_candidates: Iterable[ElectedCandidateRow] | None = None
) -> dict[str, CandidateStatistics]:

    if elected_candidates is None:
        session = object_session(election_compound)
        assert session is not None
        elected_candidates = get_elected_candidates(election_compound, session)

    year = election_compound.date.year

    def statistics(
        values: list[tuple[Gender, int | None]]
    ) -> CandidateStatistics:

        birth_years = [
            birth_year
            for _, birth_year in values
            if birth_year is not None
        ]
        age = mean(year - y for y in birth_years) if birth_years else None
        return {
            'count': len(values),
            'age': round(age) if age is not None else age
        }

    all_values = sorted(
        (
            (candidate.gender or 'undetermined', candidate.year_of_birth)
            for candidate in elected_candidates
        ),
        key=itemgetter(0)
    )

    result = {
        gender: statistics(values)
        for gender, values in groupbylist(all_values, key=itemgetter(0))
    }
    result['total'] = statistics(all_values)

    if set(result) - {'total', 'undetermined'}:
        return result

    return {}
