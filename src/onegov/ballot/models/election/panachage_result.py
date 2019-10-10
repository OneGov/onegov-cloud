from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PanachageResult(Base, TimestampMixin):

    """ Panachage Results are read in for lists and parties.

    case lists:
    It represents the votes transferred from one list to another.
    target represents list.id (UUID) and owner is NULL

    case parties:
    It represents the total of votes reveived by panachage for a party across
    all the lists.
    target represents the party name (as well as source is party name) and
    the owner is the election.id (a string).

    """

    __tablename__ = 'panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the owner of this result, maps to election.id
    # where electon.id is derived from the title

    owner = Column(Text, nullable=True)

    #: the target this result belongs to, maps to list.id
    target = Column(Text, nullable=False)

    #: the source this result belongs to, maps to list.id
    source = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
