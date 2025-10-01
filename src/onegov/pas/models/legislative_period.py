from __future__ import annotations

from onegov.core.orm import Base
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


class LegislativePeriod(Base, TimestampMixin, ORMSearchable):

    __tablename__ = 'par_legislative_periods'

    es_type_name = 'pas_legislative_period'
    es_public = False
    es_properties = {'name': {'type': 'text', 'weight': 'A'}}

    #: The polymorphic type of legislative period
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'pas_legislative_period',
    }

    @property
    def es_suggestion(self) -> str:
        return self.name

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: Column[date] = Column(
        Date,
        nullable=False
    )

    #: The end date
    end: Column[date] = Column(
        Date,
        nullable=False
    )

    #: The name
    name: Column[str] = Column(
        Text,
        nullable=False
    )
