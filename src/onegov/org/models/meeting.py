from __future__ import annotations

import uuid
from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID, MarkupText, UTCDateTime
from onegov.file import AssociatedFiles
from onegov.search import ORMSearchable
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import RelationshipProperty, relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from markupsafe import Markup
    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import MeetingItem
    from sqlalchemy.orm import Query


class Meeting(Base, ContentMixin, ORMSearchable, AssociatedFiles):

    __tablename__ = 'par_meetings'

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

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

    #: date and time of the meeting start
    start_datetime: Column[datetime | None]
    start_datetime = Column(UTCDateTime, nullable=True)

    #: date and time of the meeting end
    end_datetime: Column[datetime | None]
    end_datetime = Column(UTCDateTime, nullable=True)

    #: location address of meeting
    address: Column[Markup] = Column(MarkupText, nullable=False)

    description: Column[Markup | None] = Column(MarkupText, nullable=True)

    #: political business id
    political_business_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_political_businesses.id'),
    )

    #: list of political businesses, "Traktanden"
    political_businesses: RelationshipProperty[PoliticalBusiness] = (
        relationship(
            'PoliticalBusiness',
            back_populates='meetings',
            order_by='PoliticalBusiness.number',
            primaryjoin='Meeting.political_business_id == '
            'PoliticalBusiness.id',
        )
    )

    #: The meeting items
    meeting_items: relationship[list[MeetingItem]]
    meeting_items = relationship(
        'MeetingItem',
        cascade='all, delete-orphan',
        back_populates='meeting',
        order_by='desc(MeetingItem.number)'
    )

    def __repr__(self) -> str:
        return f'<Meeting {self.title}, {self.start_datetime}>'


class MeetingCollection(GenericCollection[Meeting]):

    @property
    def model_class(self) -> type[Meeting]:
        return Meeting

    def query(self) -> Query[Meeting]:
        query = super().query()
        return query.order_by(self.model_class.start_datetime.desc())
