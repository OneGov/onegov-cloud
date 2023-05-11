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
    from .election import Election


class ElectionRelationship(Base):
    """ A relationship between elections. """

    __tablename__ = 'election_relationships'

    #: Identifies the relationship.
    id = Column(UUID, primary_key=True, default=uuid4)

    # FIXME: should source_id and target_id be nullable=False?
    #: The source election ID.
    source_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE')
    )

    #: The target election ID.
    target_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE'),
        primary_key=True
    )

    #: The source election.
    source: 'relationship[Election]' = relationship(
        'Election',
        foreign_keys=[source_id],
        backref=backref(
            'related_elections',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    #: The target election.
    target: 'relationship[Election]' = relationship(
        'Election',
        foreign_keys=[target_id],
        backref=backref(
            'referencing_elections',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    #: the type of relationship
    type = Column(Text, nullable=True)
