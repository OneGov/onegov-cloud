from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Text
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date


class Party(Base, ContentMixin, TimestampMixin, ORMSearchable):

    __tablename__ = 'pas_parties'

    es_public = False
    es_properties = {'name': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name
    name: 'Column[str]' = Column(
        Text,
        nullable=False
    )

    #: The start date
    start: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The end date
    end: 'Column[date|None]' = Column(
        Date,
        nullable=True
    )

    #: The portrait
    portrait: 'Column[str|None]' = Column(
        Text,
        nullable=True
    )

    #: The description
    description: 'Column[str|None]' = Column(
        Text,
        nullable=True
    )
