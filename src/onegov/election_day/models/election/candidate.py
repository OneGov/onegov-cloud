from __future__ import annotations

from builtins import list as list_t
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.election_day.models.election.candidate_result import (
    CandidateResult)
from onegov.election_day.models.election.election_result import ElectionResult
from onegov.election_day.models.mixins import summarized_property
from onegov.election_day.types import Gender
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import CandidatePanachageResult
    from onegov.election_day.models import Election
    from onegov.election_day.models import List
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.types import DistrictPercentage
    from onegov.election_day.types import EntityPercentage
    from sqlalchemy.sql import ColumnElement


class Candidate(Base, TimestampMixin):
    """ A candidate. """

    __tablename__ = 'candidates'

    #: the internal id of the candidate
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the external id of the candidate
    candidate_id: Mapped[str]

    #: the family name
    family_name: Mapped[str]

    #: the first name
    first_name: Mapped[str]

    #: True if the candidate is elected
    elected: Mapped[bool]

    #: the gender
    gender: Mapped[Gender | None] = mapped_column(
        Enum(
            'male',
            'female',
            'undetermined',
            name='candidate_gender'
        )
    )

    #: the year of birth
    year_of_birth: Mapped[int | None]

    #: the election id this candidate belongs to
    election_id: Mapped[str] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
    )

    #: the election this candidate belongs to
    election: Mapped[Election] = relationship(
        back_populates='candidates'
    )

    #: the list id this candidate belongs to
    list_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('lists.id', ondelete='CASCADE')
    )

    #: the list this candidate belongs to
    list: Mapped[List] = relationship(
        back_populates='candidates'
    )

    #: the party name
    party: Mapped[str | None]

    #: a candidate contains n results
    results: Mapped[list_t[CandidateResult]] = relationship(
        cascade='all, delete-orphan',
        back_populates='candidate'
    )

    #: a (proporz) candidate contains votes from other other lists
    panachage_results: Mapped[list_t[CandidatePanachageResult]] = (
        relationship(
            cascade='all, delete-orphan',
            back_populates='candidate'
        )
    )

    #: the total votes
    votes = summarized_property('votes')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(result, attribute) for result in self.results)

    @classmethod
    def aggregate_results_expression(
        cls,
        attribute: str
    ) -> ColumnElement[int]:
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select(
            func.coalesce(
                func.sum(getattr(CandidateResult, attribute)),
                0
            )
        )
        expr = expr.where(CandidateResult.candidate_id == cls.id)
        return expr.label(attribute)

    @property
    def percentage_by_entity(self) -> dict[int, EntityPercentage]:
        """ Returns the percentage of votes by the entity. Includes uncounted
        entities and entities with no results available.

        """
        query = self.election.results_query.order_by(None)
        query = query.join(ElectionResult.candidate_results)
        query = query.filter(CandidateResult.candidate_id == self.id)

        if self.election.type == 'proporz':
            proporz_election = cast('ProporzElection', self.election)
            totals_by_entity = proporz_election.votes_by_entity.subquery()

            results_sub = query.with_entities(
                ElectionResult.entity_id.label('id'),
                ElectionResult.counted.label('counted'),
                CandidateResult.votes.label('votes')
            ).subquery()

            session = object_session(self)
            assert session is not None
            results = session.query(
                results_sub.c.id,
                results_sub.c.counted,
                totals_by_entity.c.votes.label('total'),
                results_sub.c.votes
            )
            results = results.join(
                totals_by_entity,
                totals_by_entity.c.entity_id == results_sub.c.id
            )

        else:
            results = query.with_entities(
                ElectionResult.entity_id.label('id'),
                ElectionResult.counted.label('counted'),
                ElectionResult.accounted_ballots.label('total'),
                CandidateResult.votes.label('votes')
            )

        percentage: dict[int, EntityPercentage] = {
            r.id: {
                'counted': r.counted,
                'votes': r.votes,
                'percentage': round(
                    100 * (r.votes / r.total), 2) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results_query.with_entities(
            ElectionResult.entity_id.label('id'),
            ElectionResult.counted.label('counted')
        )
        empty = empty.filter(
            ElectionResult.entity_id.notin_([r.id for r in results])
        )
        percentage.update({
            r.id: {
                'counted': r.counted,
                'percentage': 0.0,
                'votes': 0
            } for r in empty}
        )
        return percentage

    @property
    def percentage_by_district(self) -> dict[str, DistrictPercentage]:
        """ Returns the percentage of votes aggregated by the distict. Includes
        uncounted districts and districts with no results available.

        """
        query = self.election.results_query
        query = query.join(ElectionResult.candidate_results)
        query = query.filter(CandidateResult.candidate_id == self.id)

        if self.election.type == 'proporz':

            totals_by_district = self.election.votes_by_district.subquery()

            subquery = query.with_entities(
                ElectionResult.district.label('name'),
                func.array_agg(ElectionResult.entity_id).label('entities'),
                func.coalesce(
                    func.bool_and(ElectionResult.counted), False
                ).label('counted'),
                func.sum(CandidateResult.votes).label('votes'),
            )
            subquery = subquery.group_by(ElectionResult.district)
            subquery = subquery.order_by(None)

            results_sub = subquery.subquery()

            session = object_session(self)
            assert session is not None
            results = session.query(
                results_sub.c.name,
                results_sub.c.entities,
                results_sub.c.counted,
                totals_by_district.c.votes.label('total'),
                results_sub.c.votes
            )
            results = results.join(
                totals_by_district,
                totals_by_district.c.district == results_sub.c.name
            )

        else:
            results = query.with_entities(
                ElectionResult.district.label('name'),
                func.array_agg(ElectionResult.entity_id).label('entities'),
                func.coalesce(
                    func.bool_and(ElectionResult.counted), False
                ).label('counted'),
                func.sum(ElectionResult.accounted_ballots).label('total'),
                func.sum(CandidateResult.votes).label('votes'),
            )
            results = results.group_by(ElectionResult.district)
            results = results.order_by(None)

        percentage: dict[str, DistrictPercentage] = {
            r.name: {
                'counted': r.counted,
                'entities': r.entities,
                'votes': r.votes,
                'percentage': round(
                    100 * (r.votes / r.total), 2) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results_query.with_entities(
            ElectionResult.district.label('name'),
            func.array_agg(ElectionResult.entity_id).label('entities'),
            func.coalesce(
                func.bool_and(ElectionResult.counted), False
            ).label('counted')
        )
        empty = empty.group_by(ElectionResult.district)
        empty = empty.order_by(None)
        for result in empty:
            update = (
                result.name not in percentage
                or (
                    set(percentage[result.name]['entities'])
                    != set(result.entities)
                )
            )
            if update:
                percentage[result.name] = {
                    'counted': result.counted,
                    'entities': result.entities,
                    'percentage': 0.0,
                    'votes': 0
                }

        return percentage
