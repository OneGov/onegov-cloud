from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.mixins import summarized_property
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class Candidate(Base, TimestampMixin):
    """ A candidate. """

    __tablename__ = 'candidates'

    #: the internal id of the candidate
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the external id of the candidate
    candidate_id = Column(Text, nullable=False)

    #: the family name
    family_name = Column(Text, nullable=False)

    #: the first name
    first_name = Column(Text, nullable=False)

    #: True if the candidate is elected
    elected = Column(Boolean, nullable=False)

    #: the election this candidate belongs to
    election_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    #: the list this candidate belongs to
    list_id = Column(
        UUID,
        ForeignKey('lists.id', ondelete='CASCADE'),
        nullable=True
    )

    #: the party name
    party = Column(Text, nullable=True)

    #: a candidate contains n results
    results = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        backref=backref('candidate'),
        lazy='dynamic',
    )

    #: the total votes
    votes = summarized_property('votes')

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """
        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(CandidateResult, attribute))])
        expr = expr.where(CandidateResult.candidate_id == cls.id)
        expr = expr.label(attribute)
        return expr

    @property
    def percentage_by_entity(self):
        """ Returns the percentage of votes by the entity. Includes uncounted
        entities and entities with no results available.

        """

        results = self.election.results
        results = results.join(ElectionResult.candidate_results)
        results = results.filter(CandidateResult.candidate_id == self.id)
        results = results.with_entities(
            ElectionResult.entity_id.label('id'),
            ElectionResult.counted.label('counted'),
            ElectionResult.accounted_ballots.label('total'),
            CandidateResult.votes.label('votes')
        )
        results = results.all()
        percentage = {
            r.id: {
                'counted': r.counted,
                'percentage': 100 * (r.votes / r.total) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results
        empty = empty.with_entities(
            ElectionResult.entity_id.label('id'),
            ElectionResult.counted.label('counted')
        )
        empty = empty.filter(
            ElectionResult.entity_id.notin_([r.id for r in results])
        )
        percentage.update({
            r.id: {'counted': r.counted, 'percentage': 0.0} for r in empty}
        )
        return percentage

    @property
    def percentage_by_district(self):
        """ Returns the percentage of votes aggregated by the distict. Includes
        uncounted districts and districts with no results available.

        """

        results = self.election.results
        results = results.join(ElectionResult.candidate_results)
        results = results.filter(CandidateResult.candidate_id == self.id)
        results = results.with_entities(
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
        results = results.all()
        percentage = {
            r.name: {
                'counted': r.counted,
                'entities': r.entities,
                'percentage': 100 * (r.votes / r.total) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results
        empty = empty.with_entities(
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
                    'percentage': 0.0
                }

        return percentage
