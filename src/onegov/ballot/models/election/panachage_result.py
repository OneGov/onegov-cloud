from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PanachageResult(Base, TimestampMixin):

    """ Panachage Results are read in for lists and parties.

    case lists:
    It represents the votes transferred from one list to another.
    target represents list.id (UUID).

    case parties:
    It represents the total of votes reveived by panachage for a party across
    all the lists.
    target/source represents the party names.

    """

    __tablename__ = 'panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

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

    #: the target this result belongs to, maps to list.id
    target = Column(Text, nullable=False)

    #: the source this result belongs to, maps to list.id
    source = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
