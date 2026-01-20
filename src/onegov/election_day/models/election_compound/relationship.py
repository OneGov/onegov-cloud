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
    from onegov.election_day.models import ElectionCompound


class ElectionCompoundRelationship(Base):
    """ A relationship between election compounds. """

    __tablename__ = 'election_compound_relationships'

    #: Identifies the relationship.
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The source election compound ID.
    source_id: Column[str] = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE'),
        nullable=False
    )

    #: The target election compound ID.
    target_id: Column[str] = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The source election compound.
    source: relationship[ElectionCompound] = relationship(
        'ElectionCompound',
        foreign_keys=[source_id],
        back_populates='related_compounds'
    )

    #: The target election compound.
    target: relationship[ElectionCompound] = relationship(
        'ElectionCompound',
        foreign_keys=[target_id],
        back_populates='referencing_compounds'
    )

    #: the type of relationship
    type: Column[str | None] = Column(Text, nullable=True)
