from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class ElectionAssociation(Base):
    """ An association between elections.

    This might be used for example to connect different rounds of elections
    together. Using a separate table for the associations allows to add further
    attributes to association in a later stage, for example translated names,
    such as 'Erster Wahlgang'.

    """

    __tablename__ = 'election_associations'

    #: Identifies the assiciation.
    id = Column(UUID, primary_key=True, default=uuid4)

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
    source_election = relationship(
        'Election',
        foreign_keys=[source_id],
        backref=backref(
            'related_elections',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    #: The target election.
    target_election = relationship(
        'Election',
        foreign_keys=[target_id],
        backref=backref(
            'referencing_elections',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
