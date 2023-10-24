from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid

    from .election_compound import ElectionCompound


class ElectionCompoundRelationship(Base):
    """ A relationship between election compounds. """

    __tablename__ = 'election_compound_relationships'

    #: Identifies the relationship.
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # FIXME: source_id should be nullable=False
    #: The source election compound ID.
    source_id: 'Column[str]' = Column(  # type:ignore[assignment]
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE')
    )

    #: The target election compound ID.
    target_id: 'Column[str]' = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The source election compound.
    source: 'relationship[ElectionCompound]' = relationship(
        'ElectionCompound',
        foreign_keys=[source_id],
        backref=backref(
            'related_compounds',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    #: The target election compound.
    target: 'relationship[ElectionCompound]' = relationship(
        'ElectionCompound',
        foreign_keys=[target_id],
        backref=backref(
            'referencing_compounds',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    #: the type of relationship
    type: 'Column[str | None]' = Column(Text, nullable=True)
