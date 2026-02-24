from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.election_day.models.vote.mixins import DerivedAttributesMixin
from onegov.election_day.models.vote.mixins import DerivedBallotsCountMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Ballot


class BallotResult(Base, TimestampMixin, DerivedAttributesMixin,
                   DerivedBallotsCountMixin):
    """ The result of a specific ballot. Each ballot may have multiple
    results. Those results may be aggregated or not.

    """

    __tablename__ = 'ballot_results'

    #: identifies the result, may be used in the url
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The entity id (e.g. BFS number).
    entity_id: Mapped[int]

    #: the name of the entity
    name: Mapped[str]

    #: the district this entity belongs to
    district: Mapped[str | None]

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted: Mapped[bool]

    #: number of yeas, in case of variants, the number of yeas for the first
    #: option of the tie breaker
    yeas: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of nays, in case of variants, the number of nays for the first
    #: option of the tie breaker (so a yay for the second option)
    nays: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of empty votes
    empty: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of invalid votes
    invalid: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of eligible voters
    eligible_voters: Mapped[int] = mapped_column(default=lambda: 0)

    #: number of expats
    expats: Mapped[int | None]

    #: the id of the ballot this result belongs to
    ballot_id: Mapped[UUID] = mapped_column(
        ForeignKey('ballots.id', ondelete='CASCADE')
    )

    #: the ballot this result belongs to
    ballot: Mapped[Ballot] = relationship(back_populates='results')
