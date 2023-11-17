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
    from ..election import Election


class ElectionCompoundAssociation(Base):

    __tablename__ = 'election_compound_associations'

    #: identifies the candidate result
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # FIXME: election_compount_id should be nullable=False
    #: The election compound ID
    election_compound_id: 'Column[str]' = Column(  # type:ignore[assignment]
        Text,
        ForeignKey('election_compounds.id', onupdate='CASCADE')
    )

    #: The election ID
    election_id: 'Column[str]' = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    election_compound: 'relationship[ElectionCompound]' = relationship(
        'ElectionCompound', backref=backref(
            'associations',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    election: 'relationship[Election]' = relationship(
        'Election', backref=backref(
            'associations',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
