from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from uuid import uuid4


class PartyResult(Base, TimestampMixin):
    """ The election result of a party in an election for a given year. """

    __tablename__ = 'party_results'

    #: identifies the party result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the election or election compound this result belongs to
    owner = Column(Text, nullable=True)  # todo: delete me after migration!

    #: the election this result belongs to
    election_id = Column(
        Text,
        ForeignKey('elections.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    #: the election compound this result belongs to
    election_compound_id = Column(
        Text,
        ForeignKey(
            'election_compounds.id', onupdate='CASCADE', ondelete='CASCADE'
        ),
        nullable=True
    )

    #: the domain of this result
    domain = Column(Text, nullable=True)

    #: the domain segment of this result
    domain_segment = Column(Text, nullable=True)

    #: the number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    #: the number of votes
    votes = Column(Integer, nullable=False, default=lambda: 0)

    #: the number of total votes
    total_votes = Column(Integer, nullable=False, default=lambda: 0)

    #: the number of total votes divided by the total number of mandates,
    #: used instead of total_votes by election compounds
    voters_count = Column(Numeric(12, 2), nullable=True, default=lambda: 0)

    #: the voters count as percentage
    voters_count_percentage = Column(
        Numeric(12, 2), nullable=True, default=lambda: 0
    )

    #: all translations of the party name
    name_translations = Column(HSTORE, nullable=False)

    #: the name of the party (uses the locale of the request, falls back to the
    #: default locale of the app)
    name = translation_hybrid(name_translations)

    #: the year
    year = Column(Integer, nullable=False, default=lambda: 0)

    #: the id of the party
    party_id = Column(Text, nullable=False)
