from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.election_day.models import Election


class ElectionRelationship(Base):
    """ A relationship between elections. """

    __tablename__ = 'election_relationships'

    #: Identifies the relationship.
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The source election ID.
    source_id: Column[str] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        nullable=False
    )

    #: The target election ID.
    target_id: Column[str] = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The source election.
    source: relationship[Election] = relationship(
        'Election',
        foreign_keys=[source_id],
        back_populates='related_elections'
    )

    #: The target election.
    target: relationship[Election] = relationship(
        'Election',
        foreign_keys=[target_id],
        back_populates='referencing_elections'
    )

    #: the type of relationship
    type = Column(Text, nullable=True)
