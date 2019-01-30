from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


class Municipality(Base, TimestampMixin):
    """ A municipality """

    __tablename__ = 'wtfs_municipalities'

    #: the id of the db record (only relevant internally)
    id = Column(Integer, primary_key=True)

    #: The name of the municipality.
    name = Column(Text, nullable=False)

    #: The name of the municipality.
    bfs_number = Column(Integer, nullable=False)
