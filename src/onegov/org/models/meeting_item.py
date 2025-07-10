from __future__ import annotations

import uuid

from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid
    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import Meeting


class MeetingItem(Base, ORMSearchable):

    __tablename__ = 'par_meeting_items'

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
        'number': {'type': 'text'}
    }

    @property
    def es_suggestion(self) -> str:
        return self.title

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid.uuid4,
    )

    #: The title of the meeting item
    title: Column[str] = Column(Text, nullable=False)

    #: number of the meeting item
    number: Column[str | None] = Column(Text, nullable=True)

    #: political business id
    political_business_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_political_businesses.id'),
    )
    political_business: relationship[PoliticalBusiness | None] = relationship(
        'PoliticalBusiness',
        foreign_keys=[political_business_id]
    )

    #: link ID only used for mapping after import
    political_business_link_id: Column[str | None] = Column(
        Text, nullable=True)

    #: The id of the meeting
    meeting_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_meetings.id'),
        nullable=False
    )

    #: The meeting
    meeting: relationship[Meeting] = relationship(
        'Meeting',
        back_populates='meeting_items'
    )

    def __repr__(self) -> str:
        return f'<Meeting Item {self.number} {self.title}>'
