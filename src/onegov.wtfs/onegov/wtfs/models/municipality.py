from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import UserGroup
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class Municipality(Base, TimestampMixin):
    """ A municipality """

    __tablename__ = 'wtfs_municipalities'

    #: the id of the db record (only relevant internally)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The name of the municipality.
    name = Column(Text, nullable=False)

    #: The name of the municipality.
    bfs_number = Column(Integer, nullable=False)

    #: The group that holds all users of this municipality.
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=True)
    group = relationship(
        UserGroup, backref=backref('municipality', uselist=False)
    )
