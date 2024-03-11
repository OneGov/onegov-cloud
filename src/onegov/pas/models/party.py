from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from uuid import uuid4


class Party(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'pas_parties'

    #: Internal ID
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the name
    name = Column(Text, nullable=False)

    #: The start date
    start = Column(Date, nullable=False)

    #: The end date
    end = Column(Date, nullable=False)

    #: The description
    description = Column(Text, nullable=True)
