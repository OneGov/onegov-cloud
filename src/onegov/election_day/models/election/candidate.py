from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.election_day.models.election.candidate_result import \
    CandidateResult
from onegov.election_day.models.election.election_result import ElectionResult
from onegov.election_day.models.mixins import summarized_property
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import CandidatePanachageResult
    from onegov.election_day.models import Election
    from onegov.election_day.models import List
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.types import DistrictPercentage
    from onegov.election_day.types import EntityPercentage
    from onegov.election_day.types import Gender
    from sqlalchemy.sql import ColumnElement
    import uuid

    list_t = list


class Candidate(Base, TimestampMixin):
    """ A candidate. """

    __tablename__ = 'candidates'

    #: the internal id of the candidate
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the external id of the candidate
    candidate_id: Column[str] = Column(Text, nullable=False)

    #: the family name
    family_name: Column[str] = Column(Text, nullable=False)

    #: the first name
    first_name: Column[str] = Column(Text, nullable=False)

    #: True if the candidate is elected
    elected: Column[bool] = Column(Boolean, nullable=False)

    #: the gender
    gender: Column[Gender | None] = Column(
        Enum(  # type:ignore[arg-type]
            'male',
            'female',
            'undetermined',
            name='candidate_gender'
        ),
        nullable=True
    )

    #: the year of birth
    year_of_birth: Column[int | None] = Column(Integer, nullable=True)

    #: the election id this candidate belongs to
    election_id: Column[str] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    #: the election this candidate belongs to
    election: relationship[Election] = relationship(
        'Election',
        back_populates='candidates'
    )

    #: the list id this candidate belongs to
    list_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=True
    )

    #: the list this candidate belongs to
    list: relationship[List] = relationship(
        'List',
        back_populates='candidates'
    )

    #: the party name
    party: Column[str | None] = Column(Text, nullable=True)

    #: a candidate contains n results
    results: relationship[list_t[CandidateResult]] = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        back_populates='candidate'
    )

    #: a (proporz) candidate contains votes from other other lists
    panachage_results: relationship[list_t[CandidatePanachageResult]] = (
        relationship(
            'CandidatePanachageResult',
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

        expr = select([
            func.coalesce(
                func.sum(getattr(CandidateResult, attribute)),
                0
            )
        ])
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

            query = query.with_entities(
                ElectionResult.district.label('name'),
                func.array_agg(ElectionResult.entity_id).label('entities'),
                func.coalesce(
                    func.bool_and(ElectionResult.counted), False
                ).label('counted'),
                func.sum(CandidateResult.votes).label('votes'),
            )
            query = query.group_by(ElectionResult.district)
            query = query.order_by(None)

            results_sub = query.subquery()

            session = object_session(self)
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
