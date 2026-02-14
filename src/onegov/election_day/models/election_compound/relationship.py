from __future__ import annotations

from onegov.core.orm import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import ElectionCompound


class ElectionCompoundRelationship(Base):
    """ A relationship between election compounds. """

    __tablename__ = 'election_compound_relationships'

    #: Identifies the relationship.
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The source election compound ID.
    source_id: Mapped[str] = mapped_column(
        ForeignKey('election_compounds.id', onupdate='CASCADE')
    )

    #: The target election compound ID.
    target_id: Mapped[str] = mapped_column(
        ForeignKey('election_compounds.id', onupdate='CASCADE')
    )

    #: The source election compound.
    source: Mapped[ElectionCompound] = relationship(
        foreign_keys=[source_id],
        back_populates='related_compounds'
    )

    #: The target election compound.
    target: Mapped[ElectionCompound] = relationship(
        foreign_keys=[target_id],
        back_populates='referencing_compounds'
    )

    #: the type of relationship
    type: Mapped[str | None]
