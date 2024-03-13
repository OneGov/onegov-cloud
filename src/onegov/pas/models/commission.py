from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from uuid import uuid4
from sqlalchemy import Enum


TYPES = {
    'normal': _('normal'),
    'intercantonal': _('intercantonal'),
    'official': _('official mission'),
}


class Commission(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_commissions'

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

    #: The type
    type = Column(
        Enum(*TYPES, name='pas_commission_type'),
        nullable=False,
        default='normal'
    )

    @property
    def type_label(self) -> str:
        return TYPES.get(self.type, '')

    #: The description
    description = Column(Text, nullable=True)
