from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


class PanachageResult(Base, TimestampMixin):

    """ The votes transferred from one list to another. """

    __tablename__ = 'panachage_results'

    #: identifies the result
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the owner of this result
    owner = Column(Text, nullable=True)

    #: the target this result belongs to
    target = Column(Text, nullable=False)

    #: the source this result belongs to
    source = Column(Text, nullable=False)

    # votes
    votes = Column(Integer, nullable=False, default=lambda: 0)
