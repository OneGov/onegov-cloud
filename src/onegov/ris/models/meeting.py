from __future__ import annotations

import uuid

from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import RelationshipProperty, relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID, MarkupText, UTCDateTime
from onegov.search import ORMSearchable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from markupsafe import Markup
    from datetime import datetime

    from onegov.ris.models.political_business import RISPoliticalBusiness


class RISMeeting(Base, ContentMixin, ORMSearchable):
    __tablename__ = 'ris_meetings'

    es_public = True
    es_properties = {'title_text': {'type': 'text'}}

    @property
    def es_suggestion(self) -> str:
        return self.title

    @property
    def title_text(self) -> str:
        return f'{self.title} ({self.start_datetime})'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid.uuid4,
    )

    #: The title of the meeting
    title: Column[str] = Column(Text, nullable=False)

    #: date and time of the meeting
    start_datetime: Column[datetime | None]
    start_datetime = Column(UTCDateTime, nullable=True)

    #: location address of meeting
    address: Column[str] = Column(Text, nullable=False)

    description: Column[Markup | None] = Column(MarkupText, nullable=True)

    #: political business id
    political_business_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_political_businesses.id'),
    )

    #: list of political businesses, "Traktanden"
    political_businesses: RelationshipProperty[RISPoliticalBusiness] = (
        relationship(
            'RISPoliticalBusiness',
            back_populates='meetings',
            order_by='RISPoliticalBusiness.number',
            primaryjoin='RISMeeting.political_business_id == '
            'RISPoliticalBusiness.id',
        )
    )

    def __repr__(self) -> str:
        return f'<Meeting {self.title}, {self.start_datetime}>'
