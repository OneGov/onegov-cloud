from __future__ import annotations

import uuid
from functools import cached_property

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from sedate import utcnow

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property, content_property
from onegov.core.orm.types import UUID, MarkupText, UTCDateTime
from onegov.file import MultiAssociatedFiles
from onegov.org import _
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.search import ORMSearchable
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import RelationshipProperty, relationship

from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from markupsafe import Markup

    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session

    from onegov.org.models import PoliticalBusiness
    from onegov.org.models import MeetingItem


class Meeting(
    AccessExtension,
    MultiAssociatedFiles,
    Base,
    ContentMixin,
    GeneralFileLinkExtension,
    ORMSearchable,
):

    __tablename__ = 'par_meetings'

    es_public = True
    es_properties = {
        'title_text': {'type': 'text', 'weight': 'A'},
        'display_name': {'type': 'text', 'weight': 'A'}
    }

    @property
    def es_suggestion(self) -> list[str]:
        return [self.title_text, self.display_name]

    @property
    def es_last_change(self) -> datetime | None:
        # NOTE: More current meetings should be more relevant
        # FIXME: Should we de-prioritize meetings without a date
        #        or maybe even exclude them from search results?
        #        Currently they would be as relevant as current
        #        meetings.
        return self.start_datetime

    @property
    def title_text(self) -> str:
        return f'{self.title} ({self.start_datetime})'

    @property
    def display_name(self) -> str:
        # return title and start_datetime as dmY
        return f'{self.title} {self.start_datetime:%d.%m.%Y}'

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

    #: link to audio url
    audio_link: dict_property[str] = content_property(default='')

    #: link to video url
    video_link: dict_property[str] = content_property(default='')

    @hybrid_property
    def past(self):
        return self.start_datetime < utcnow() if self.start_datetime else False

    @past.expression  # type:ignore[no-redef]
    def past(cls):
        return cls.start_datetime < func.now()

    def __repr__(self) -> str:
        return f'<Meeting {self.title}, {self.start_datetime}>'


class MeetingCollection(GenericCollection[Meeting]):

    def __init__(
        self,
        session: Session,
        past: bool | None = None
    ) -> None:
        super().__init__(session)
        self.past = past

    @cached_property
    def title(self) -> str:
        return _('Meeting')

    @property
    def model_class(self) -> type[Meeting]:
        return Meeting

    def query(self) -> Query[Meeting]:
        query = super().query()

        Meeting = self.model_class  # noqa: N806
        if self.past is not None:
            if self.past:
                query = query.filter(Meeting.start_datetime < utcnow())
                query = query.order_by(Meeting.start_datetime.desc())
            else:
                query = query.filter(Meeting.start_datetime >= utcnow())
                query = query.order_by(Meeting.start_datetime.asc())

        return query

    def for_filter(self, past: bool | None = None) -> Self:
        return self.__class__(self.session, past=past)
