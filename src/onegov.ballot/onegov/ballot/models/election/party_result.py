from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PartyResult(Base, TimestampMixin):
    """ The election result of a party in an election for a given year. """

    __tablename__ = 'party_results'

    #: identifies the party result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election this result belongs to
    election_id = Column(Text, ForeignKey('elections.id'), nullable=False)

    # number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    # total votes
    total_votes = Column(Integer, nullable=False, default=lambda: 0)

    #: name of the party
    name = Column(Text, nullable=False)

    #: year
    year = Column(Integer, nullable=False, default=lambda: 0)

    #: color code
    color = Column(Text, nullable=True)
