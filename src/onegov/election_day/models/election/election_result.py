from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.election_day.models.election.mixins import DerivedAttributesMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from onegov.election_day.models import CandidatePanachageResult
    from onegov.election_day.models import CandidateResult
    from onegov.election_day.models import Election
    from onegov.election_day.models import ListResult
    from sqlalchemy.sql import ColumnElement


class ElectionResult(Base, TimestampMixin, DerivedAttributesMixin):
    """ The election result in a single political entity. """

    __tablename__ = 'election_results'

    #: identifies the result
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the election id this result belongs to
    election_id: Column[str] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    #: the election this candidate belongs to
    election: relationship[Election] = relationship(
        'Election',
        back_populates='results'
    )

    #: entity id (e.g. a BFS number).
    entity_id: Column[int] = Column(Integer, nullable=False)

    #: the name of the entity
    name: Column[str] = Column(Text, nullable=False)

    #: the district this entity belongs to
    district: Column[str | None] = Column(Text, nullable=True)

    #: the superregion this entity belongs to
    superregion: Column[str | None] = Column(Text, nullable=True)

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted: Column[bool] = Column(Boolean, nullable=False)

    #: number of eligible voters
    eligible_voters: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of expats
    expats: Column[int | None] = Column(
        Integer,
        nullable=True
    )

    #: number of received ballots
    received_ballots: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of blank ballots
    blank_ballots: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of invalid ballots
    invalid_ballots: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of blank votes
    blank_votes: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of invalid votes
    invalid_votes: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    if TYPE_CHECKING:
        accounted_votes: Column[int]

    @hybrid_property  # type:ignore[no-redef]
    def accounted_votes(self) -> int:
        """ The number of accounted votes. """

        return (
                self.election.number_of_mandates * self.accounted_ballots
                - self.blank_votes
                - self.invalid_votes
        )

    @accounted_votes.expression  # type:ignore[no-redef]
    def accounted_votes(cls) -> ColumnElement[int]:
        """ The number of accounted votes. """
        from onegov.election_day.models import Election  # circular

        # A bit of a hack :|
        number_of_mandates = select(
            [Election.number_of_mandates],
            whereclause=text('elections.id = election_results.election_id')
        ).scalar_subquery()
        return (
                number_of_mandates * (
                cls.received_ballots - cls.blank_ballots - cls.invalid_ballots
        ) - cls.blank_votes - cls.invalid_votes
        )

    #: an election result may contain n list results
    list_results: relationship[list[ListResult]] = relationship(
        'ListResult',
        cascade='all, delete-orphan',
        back_populates='election_result'
    )

    #: an election result contains n candidate results
    candidate_results: relationship[list[CandidateResult]] = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        back_populates='election_result'
    )

    #: an election result contains n candidate panachage results
    candidate_panachage_results: (
        relationship[list[CandidatePanachageResult]]) = (
        relationship(
            'CandidatePanachageResult',
            cascade='all, delete-orphan',
            back_populates='election_result'
        )
    )
