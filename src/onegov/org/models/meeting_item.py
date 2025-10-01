from __future__ import annotations

import uuid
from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import Meeting
    from sqlalchemy.orm import Query


class MeetingItem(Base, ORMSearchable):

    __tablename__ = 'par_meeting_items'

    es_public = True
    es_properties = {
        'title': {'type': 'text', 'weight': 'A'},
        'number': {'type': 'text', 'weight': 'A'}
    }

    @property
    def es_suggestion(self) -> str:
        return self.title

    @property
    def es_last_change(self) -> datetime | None:
        # NOTE: More current meetings should be more relevant
        # FIXME: Should we de-prioritize meetings without a date
        #        or maybe even exclude them from search results?
        #        Currently they would be as relevant as current
        #        meetings.
        # FIXME: This could slow down indexing quite a bit, does it
        #        result in significantly better results? Maybe we
        #        shouldn't index individual meeting items and instead
        #        add their numbers and texts to the index for the
        #        meeting itself, so you can find meetings by their
        #        meeting items, which might be what you want anyways.
        return self.meeting.start_datetime

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
        foreign_keys=[political_business_id],
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

    @property
    def display_name(self) -> str:
        return f'{self.number} {self.title}' if self.number else self.title

    def __repr__(self) -> str:
        return f'<Meeting Item {self.number} {self.title}>'


class MeetingItemCollection(GenericCollection[MeetingItem]):

    @property
    def model_class(self) -> type[MeetingItem]:
        return MeetingItem

    def query(self) -> Query[MeetingItem]:
        query = super().query()
        return query.order_by(self.model_class.number)
