from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.landsgemeinde import _
from onegov.landsgemeinde.models.file import LandsgemeindeFile
from onegov.landsgemeinde.models.votum import Votum
from onegov.search import ORMSearchable
from sedate import to_timezone
from sedate import utcnow
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import Time
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t
    from datetime import time
    from onegov.landsgemeinde.models import Assembly
    from translationstring import TranslationString
    from typing_extensions import TypeAlias

    AgendaItemState: TypeAlias = Literal['scheduled', 'ongoing', 'completed']


STATES: dict['AgendaItemState', 'TranslationString'] = {
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class AgendaItem(
    Base, ContentMixin, TimestampMixin, AssociatedFiles, ORMSearchable
):

    __tablename__ = 'landsgemeinde_agenda_items'

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
        'overview': {'type': 'localized_html'},
        'text': {'type': 'localized_html'},
        'resolution': {'type': 'localized_html'},
    }

    #: the internal id of the agenda item
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the external id of the agenda item
    number: 'Column[int]' = Column(Integer, nullable=False)

    #: the state of the agenda item
    state: 'Column[AgendaItemState]' = Column(
        Enum(*STATES.keys(), name='agenda_item_state'),  # type:ignore
        nullable=False
    )

    #: True if the item has been declared irrelevant
    irrelevant: 'Column[bool]' = Column(Boolean, nullable=False, default=False)

    #: True if the item has been tacitly accepted
    tacitly_accepted: 'Column[bool]' = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: the assembly this agenda item belongs to
    assembly_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(
            'landsgemeinde_assemblies.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    assembly: 'relationship[Assembly]' = relationship(
        'Assembly',
        back_populates='agenda_items',
    )

    #: Title of the agenda item (not translated)
    title: 'Column[str]' = Column(Text, nullable=False, default=lambda: '')

    #: The memorial of the assembly
    memorial_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The page number on which the agenda item can be found
    memorial_page: dict_property[int | None] = content_property()

    #: The overview (text) over the agenda item
    overview: dict_property[str | None] = content_property()

    #: The main content (text) of the agenda item
    text: dict_property[str | None] = content_property()

    #: The resolution (text) of the agenda item
    resolution: dict_property[str | None] = content_property()

    #: The resolution (tags) of the agenda item
    resolution_tags: dict_property[list[str] | None] = content_property()

    #: The video timestamp of this agenda item
    video_timestamp: dict_property[str | None] = content_property()

    #: An agenda item contains n vota
    vota: 'relationship[list[Votum]]' = relationship(
        Votum,
        cascade='all, delete-orphan',
        back_populates='agenda_item',
        order_by='Votum.number',
    )

    #: The local start time
    start_time: 'Column[time | None]' = Column(Time)

    def start(self) -> None:
        self.start_time = to_timezone(utcnow(), 'Europe/Zurich').time()

    #: The timestamp of the last modification
    last_modified = Column(UTCDateTime)

    def stamp(self) -> None:
        self.last_modified = self.timestamp()

    @property
    def date(self) -> 'date_t':
        return self.assembly.date

    @property
    def title_parts(self) -> list[str]:
        return [
            stripped_line
            for line in (self.title or '').splitlines()
            if (stripped_line := line.strip())
        ]

    @property
    def video_url(self) -> str | None:
        video_url = self.assembly.video_url
        if video_url:
            return f'{video_url}#t={self.video_timestamp}'
        return None
