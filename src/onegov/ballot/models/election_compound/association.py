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
    from onegov.ballot.models.election_compound import ElectionCompound
    from onegov.ballot.models.election import Election


class ElectionCompoundAssociation(Base):

    __tablename__ = 'election_compound_associations'

    #: identifies the candidate result
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The election compound ID
    election_compound_id: 'Column[str]' = Column(
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE'),
        nullable=False
    )

    #: The election ID
    election_id: 'Column[str]' = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The election compound
    election_compound: 'relationship[ElectionCompound]' = relationship(
        'ElectionCompound',
        back_populates='associations'
    )

    #: The election ID
    election: 'relationship[Election]' = relationship(
        'Election',
        back_populates='associations',
    )
