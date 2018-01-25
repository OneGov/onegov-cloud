from onegov.core.orm import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


class WinterthurStreet(Base):

    __tablename__ = 'winterthur_streets'

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(Text, nullable=False)
