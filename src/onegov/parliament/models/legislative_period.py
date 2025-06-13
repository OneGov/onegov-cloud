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

    legislative_period_type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': legislative_period_type,
        'polymorphic_identity': 'generic',
    }

    es_public = True
    es_properties = {'name': {'type': 'text'}}

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
