from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.pas.i18n import _
from onegov.search import ORMSearchable
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


class LegislativePeriod(Base, TimestampMixin, ORMSearchable):

    __tablename__ = 'par_legislative_periods'

    fts_type_title = _('Legislative periods')
    fts_public = False
    fts_title_property = 'name'
    fts_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def fts_suggestion(self) -> str:
        return self.name

    #: The polymorphic type of legislative period
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'pas_legislative_period',
    }

    @property
    def title(self) -> str:
        return self.name

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The start date
    start: Mapped[date]

    #: The end date
    end: Mapped[date]

    #: The name
    name: Mapped[str]
