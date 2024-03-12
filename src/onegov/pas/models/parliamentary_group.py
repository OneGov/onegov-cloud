from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from uuid import uuid4


class ParliamentaryGroup(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_parliamentary_groups'

    es_public = False
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the name
    name = Column(Text, nullable=False)

    #: The start date
    start = Column(Date, nullable=True)

    #: The end date
    end = Column(Date, nullable=True)

    #: The description
    description = Column(Text, nullable=True)
