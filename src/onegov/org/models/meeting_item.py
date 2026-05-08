from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.org.i18n import _
from onegov.search import ORMSearchable
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import Meeting
    from sqlalchemy.orm import Query


class MeetingItem(Base, ORMSearchable):

    __tablename__ = 'par_meeting_items'

    fts_type_title = _('Agenda')
    fts_public = True
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'text', 'weight': 'A'},
        'number': {'type': 'text', 'weight': 'A'}
    }

    @property
    def fts_suggestion(self) -> str:
        return self.title

    @property
    def fts_last_change(self) -> datetime | None:
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
        if self.meeting is None:
            return None  # type:ignore[unreachable]

        return self.meeting.start_datetime

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    #: The title of the meeting item
    title: Mapped[str]

    #: number of the meeting item
    number: Mapped[str | None]

    #: political business id
    political_business_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('par_political_businesses.id')
    )
    political_business: Mapped[PoliticalBusiness | None] = relationship(
        foreign_keys=[political_business_id],
    )

    #: link ID only used for mapping after import
    political_business_link_id: Mapped[str | None]

    #: The id of the meeting
    meeting_id: Mapped[UUID] = mapped_column(ForeignKey('par_meetings.id'))

    #: The meeting
    meeting: Mapped[Meeting] = relationship(back_populates='meeting_items')

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
