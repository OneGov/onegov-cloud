from onegov.ballot.models.election.mixins import DerivedAttributesMixin
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class ElectionResult(Base, TimestampMixin, DerivedAttributesMixin):
    """ The election result in a single political entity. """

    __tablename__ = 'election_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey('elections.id'), nullable=False)

    #: groups the result in whatever structure makes sense
    group = Column(Text, nullable=False)

    #: entity id (e.g. a BFS number).
    entity_id = Column(Integer, nullable=False)

    #: number of elegible voters
    elegible_voters = Column(Integer, nullable=False, default=lambda: 0)

    #: number of received ballots
    received_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of blank ballots
    blank_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid ballots
    invalid_ballots = Column(Integer, nullable=False, default=lambda: 0)

    #: number of blank votes
    blank_votes = Column(Integer, nullable=False, default=lambda: 0)

    #: number of invalid votes
    invalid_votes = Column(Integer, nullable=False, default=lambda: 0)

    @hybrid_property
    def accounted_votes(self):
        """ The number of accounted votes. """

        return (
            self.election.number_of_mandates * self.accounted_ballots -
            self.blank_votes - self.invalid_votes
        )

    @accounted_votes.expression
    def accounted_votes(cls):
        """ The number of accounted votes. """
        from onegov.ballot.models.election import Election  # circular

        # A bit of a hack :|
        number_of_mandates = select(
            [Election.number_of_mandates],
            whereclause='elections.id = election_results.election_id'
        )
        return (
            number_of_mandates * (
                cls.received_ballots - cls.blank_ballots - cls.invalid_ballots
            ) - cls.blank_votes - cls.invalid_votes
        )

    #: an election result may contain n list results
    list_results = relationship(
        'ListResult',
        cascade='all, delete-orphan',
        backref=backref('election_result'),
        lazy='dynamic',
    )

    #: an election result contains n candidate results
    candidate_results = relationship(
        'CandidateResult',
        cascade='all, delete-orphan',
        backref=backref('election_result'),
        lazy='dynamic',
    )
