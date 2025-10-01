from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.landsgemeinde import _
from onegov.landsgemeinde.models.agenda import AgendaItem
from onegov.landsgemeinde.models.file import LandsgemeindeFile
from onegov.landsgemeinde.models.mixins import StartTimeMixin
from onegov.search import ORMSearchable
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t
    from datetime import datetime
    from translationstring import TranslationString
    from typing import TypeAlias

    AssemblyState: TypeAlias = Literal[
        'draft', 'scheduled', 'ongoing', 'completed']


STATES: dict[AssemblyState, TranslationString] = {
    'draft': _('draft'),
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class Assembly(
    Base, ContentMixin, TimestampMixin, AssociatedFiles, ORMSearchable,
    StartTimeMixin
):

    __tablename__ = 'landsgemeinde_assemblies'

    es_public = True
    es_properties = {
        'overview': {'type': 'localized_html', 'weight': 'A'},
    }

    @property
    def es_suggestion(self) -> tuple[str, ...]:
        return (
            str(self.date.year),
            f'Landsgemeinde {self.date.year}',
        )

    #: Internal number of the event
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the state of the assembly
    state: Column[AssemblyState] = Column(
        Enum(*STATES.keys(), name='assembly_state'),  # type:ignore[arg-type]
        nullable=False
    )

    #: The date of the assembly
    date: Column[date_t] = Column(Date, nullable=False, unique=True)

    #: True if this is an extraordinary assembly
    extraordinary: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: The video URL of the assembly
    video_url: Column[str | None] = Column(Text, nullable=True)

    #: The memorial of the assembly
    memorial_pdf = NamedFile(cls=LandsgemeindeFile)

    #: An optional second part of the memorial of the assembly
    memorial_2_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The supplement to the memorial of the assembly
    memorial_supplement_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The protocol of the assembly
    protocol_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The audio of the assembly as MP3
    audio_mp3 = NamedFile(cls=LandsgemeindeFile)

    #: The audio of the assembly as ZIP
    audio_zip = NamedFile(cls=LandsgemeindeFile)

    #: The overview (text) over the assembly
    overview = dict_markup_property('content')

    #: An assembly contains n agenda items
    agenda_items: relationship[list[AgendaItem]] = relationship(
        AgendaItem,
        cascade='all, delete-orphan',
        back_populates='assembly',
        order_by='AgendaItem.number',
    )

    last_modified: Column[datetime | None] = Column(UTCDateTime)

    def stamp(self) -> None:
        self.last_modified = self.timestamp()
