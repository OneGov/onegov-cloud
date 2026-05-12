from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.election_day.models.election.mixins import DerivedAttributesMixin
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.election_day.models import CandidatePanachageResult
    from onegov.election_day.models import CandidateResult
    from onegov.election_day.models import Election
    from onegov.election_day.models import ListResult
    from sqlalchemy.sql import ColumnElement


class ElectionResult(Base, TimestampMixin, DerivedAttributesMixin):
    """ The election result in a single political entity. """

    __tablename__ = 'election_results'

    #: identifies the result
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the election id this result belongs to
    election_id: Mapped[str] = mapped_column(
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    #: the election this candidate belongs to
    election: Mapped[Election] = relationship(
        back_populates='results'
    )

    #: entity id (e.g. a BFS number).
    entity_id: Mapped[int]

    #: the name of the entity
    name: Mapped[str]

    #: the district this entity belongs to
    district: Mapped[str | None]

    #: the superregion this entity belongs to
    superregion: Mapped[str | None]

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted: Mapped[bool]

    #: number of eligible voters
    eligible_voters: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of expats
    expats: Mapped[int | None]

    #: number of received ballots
    received_ballots: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of blank ballots
    blank_ballots: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of invalid ballots
    invalid_ballots: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of blank votes
    blank_votes: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of invalid votes
    invalid_votes: Mapped[int] = mapped_column(default=lambda: 0)

    @hybrid_property
    def accounted_votes(self) -> int:
        """ The number of accounted votes. """

        return (
                self.election.number_of_mandates * self.accounted_ballots
                - self.blank_votes
                - self.invalid_votes
        )

    @accounted_votes.inplace.expression
    @classmethod
    def _accounted_votes_expression(cls) -> ColumnElement[int]:
        """ The number of accounted votes. """
        from onegov.election_day.models import Election  # circular

        # A bit of a hack :|
        number_of_mandates = select(
            Election.number_of_mandates
        ).where(text(
            'elections.id = election_results.election_id'
        )).scalar_subquery()
        return (
            number_of_mandates * (
                cls.received_ballots - cls.blank_ballots - cls.invalid_ballots
            ) - cls.blank_votes - cls.invalid_votes
        )

    #: an election result may contain n list results
    list_results: Mapped[list[ListResult]] = relationship(
        cascade='all, delete-orphan',
        back_populates='election_result'
    )

    #: an election result contains n candidate results
    candidate_results: Mapped[list[CandidateResult]] = relationship(
        cascade='all, delete-orphan',
        back_populates='election_result'
    )

    #: an election result contains n candidate panachage results
    candidate_panachage_results: Mapped[list[CandidatePanachageResult]] = (
        relationship(
            cascade='all, delete-orphan',
            back_populates='election_result'
        )
    )
