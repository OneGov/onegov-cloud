from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.list_result import ListResult
from onegov.ballot.models.mixins import summarized_property
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.orm import backref, object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.ballot.types import DistrictPercentage
    from onegov.ballot.types import EntityPercentage
    from onegov.core.types import AppenderQuery
    from sqlalchemy.sql import ColumnElement

    from .candidate import Candidate
    from .election import Election
    from .list_connection import ListConnection
    from .list_panachage_result import ListPanachageResult
    from .proporz_election import ProporzElection

    rel = relationship


class List(Base, TimestampMixin):
    """ A list. """

    __tablename__ = 'lists'

    #: internal id of the list
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: external id of the list
    list_id: 'Column[str]' = Column(Text, nullable=False)

    # number of mandates
    number_of_mandates: 'Column[int]' = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: name of the list
    name: 'Column[str]' = Column(Text, nullable=False)

    #: the election this result belongs to
    election_id: 'Column[str]' = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    #: the list connection id
    connection_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('list_connections.id', ondelete='CASCADE'),
        nullable=True
    )

    #: a list contains n candidates
    candidates: 'rel[AppenderQuery[Candidate]]' = relationship(
        'Candidate',
        cascade='all, delete-orphan',
        backref=backref('list'),
        lazy='dynamic',
    )

    #: a list contains n results
    results: 'rel[AppenderQuery[ListResult]]' = relationship(
        'ListResult',
        cascade='all, delete-orphan',
        backref=backref('list'),
        lazy='dynamic',
    )

    #: a (proporz) list contains votes from other other lists
    panachage_results: 'rel[AppenderQuery[ListPanachageResult]]'
    panachage_results = relationship(
        'ListPanachageResult',
        foreign_keys='ListPanachageResult.target_id',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    if TYPE_CHECKING:
        # backref
        election: relationship[Election]
        election_result: relationship[ElectionResult]
        connection: relationship[ListConnection | None]

    #: the total votes
    votes = summarized_property('votes')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(
        cls: 'List',
        attribute: str
    ) -> 'ColumnElement[int]':
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([
            func.coalesce(
                func.sum(getattr(ListResult, attribute)),
                0
            )
        ])
        expr = expr.where(ListResult.list_id == cls.id)
        return expr.label(attribute)

    @property
    def percentage_by_entity(self) -> dict[int, 'EntityPercentage']:
        """ Returns the percentage of votes by the entity. Includes uncounted
        entities and entities with no results available.

        """
        query = self.election.results
        query = query.join(ElectionResult.list_results)
        query = query.filter(ListResult.list_id == self.id)

        if self.election.type == 'proporz':
            proporz_election = cast('ProporzElection', self.election)
            totals_by_entity = proporz_election.votes_by_entity.subquery()
            results_sub = query.with_entities(
                ElectionResult.entity_id.label('id'),
                ElectionResult.counted.label('counted'),
                ListResult.votes.label('votes')
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
                ListResult.votes.label('votes')
            )

        percentage: dict[int, 'EntityPercentage'] = {
            r.id: {
                'counted': r.counted,
                'votes': r.votes,
                'percentage': round(
                    100 * (r.votes / r.total), 2) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results.with_entities(
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
    def percentage_by_district(self) -> dict[str, 'DistrictPercentage']:
        """ Returns the percentage of votes aggregated by the distict. Includes
        uncounted districts and districts with no results available.

        """

        query = self.election.results.order_by(None)
        query = query.join(ElectionResult.list_results)
        query = query.filter(ListResult.list_id == self.id)

        if self.election.type == 'proporz':
            totals_by_district = self.election.votes_by_district.subquery()
            query = query.with_entities(
                ElectionResult.district.label('name'),
                func.sum(ListResult.votes).label('votes'),
            )
            query = query.group_by(ElectionResult.district)
            results_sub = query.subquery()

            session = object_session(self)
            results = session.query(
                results_sub.c.name,
                totals_by_district.c.entities,
                totals_by_district.c.counted,
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
                func.sum(ElectionResult.accounted_votes).label('total'),
                func.sum(ListResult.votes).label('votes'),
            )
            results = results.group_by(ElectionResult.district)

        percentage: dict[str, 'DistrictPercentage'] = {
            r.name: {
                'counted': r.counted,
                'entities': r.entities,
                'votes': r.votes,
                'percentage': round(
                    100 * (r.votes / r.total), 2) if r.total else 0.0
            } for r in results
        }

        empty = self.election.results.with_entities(
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
