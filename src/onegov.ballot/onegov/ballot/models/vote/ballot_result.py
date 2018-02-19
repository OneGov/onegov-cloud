from onegov.ballot.models.vote.mixins import DerivedAttributesMixin
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class BallotResult(Base, TimestampMixin, DerivedAttributesMixin,
                   DerivedBallotsCountMixin):
    """ The result of a specific ballot. Each ballot may have multiple
    results. Those results may be aggregated or not.

    """

    __tablename__ = 'ballot_results'

    #: identifies the result, may be used in the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The entity id (e.g. BFS number).
    entity_id = Column(Integer, nullable=False)

    #: the name of the entity
    name = Column(Text, nullable=False)

    #: the district this entity belongs to
    district = Column(Text, nullable=True)

    #: True if the result has been counted and no changes will be made anymore.
    #: If the result is definite, all the values below must be specified.
    counted = Column(Boolean, nullable=False)

    #: number of yeas, in case of variants, the number of yeas for the first
    #: option of the tie breaker
    yeas = Column(Integer, nullable=False, default=lambda: 0)

    #: number of nays, in case of variants, the number of nays for the first
    #: option of the tie breaker (so a yay for the second option)
    nays = Column(Integer, nullable=False, default=lambda: 0)

    #: number of empty votes
    empty = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid votes
    invalid = Column(Integer, nullable=False, default=lambda: 0)

    #: number of eligible voters
    eligible_voters = Column(Integer, nullable=False, default=lambda: 0)

    #: the ballot this result belongs to
    ballot_id = Column(UUID, ForeignKey('ballots.id'), nullable=False)
