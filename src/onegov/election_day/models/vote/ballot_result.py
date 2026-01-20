from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.election_day.models.vote.mixins import DerivedAttributesMixin
from onegov.election_day.models.vote.mixins import DerivedBallotsCountMixin
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.election_day.models import Ballot


class BallotResult(Base, TimestampMixin, DerivedAttributesMixin,
                   DerivedBallotsCountMixin):
    """ The result of a specific ballot. Each ballot may have multiple
    results. Those results may be aggregated or not.

    """

    __tablename__ = 'ballot_results'

    #: identifies the result, may be used in the url
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The entity id (e.g. BFS number).
    entity_id: Column[int] = Column(Integer, nullable=False)

    #: the name of the entity
    name: Column[str] = Column(Text, nullable=False)

    #: the district this entity belongs to
    district: Column[str | None] = Column(Text, nullable=True)

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted: Column[bool] = Column(Boolean, nullable=False)

    #: number of yeas, in case of variants, the number of yeas for the first
    #: option of the tie breaker
    yeas: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: number of nays, in case of variants, the number of nays for the first
    #: option of the tie breaker (so a yay for the second option)
    nays: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: number of empty votes
    empty: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid votes
    invalid: Column[int] = Column(Integer, nullable=False, default=lambda: 0)

    #: number of eligible voters
    eligible_voters: Column[int] = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    #: number of expats
    expats: Column[int | None] = Column(Integer, nullable=True)

    #: the id of the ballot this result belongs to
    ballot_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ballots.id', ondelete='CASCADE'),
        nullable=False
    )

    #: the ballot this result belongs to
    ballot: relationship[Ballot] = relationship(
        'Ballot',
        back_populates='results'
    )
