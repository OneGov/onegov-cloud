from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from uuid import uuid4


class LegislativePeriod(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_legislative_periods'

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

    #: The start date
    start = Column(Date, nullable=False)

    #: The end date
    end = Column(Date, nullable=False)

    #: The name
    name = Column(Text, nullable=False)
