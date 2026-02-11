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
from onegov.landsgemeinde.observer import observes
from onegov.org.models.extensions import SidebarLinksExtension
from onegov.search import ORMSearchable
from sedate import as_datetime
from sedate import standardize_date
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified
from uuid import uuid4


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t
    from datetime import datetime
    from onegov.file.models.file import File
    from onegov.landsgemeinde.request import LandsgemeindeRequest
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
    StartTimeMixin, SidebarLinksExtension
):

    __tablename__ = 'landsgemeinde_assemblies'

    fts_public = True
    fts_title_property = None
    fts_properties = {
        'overview': {'type': 'localized', 'weight': 'A'},
    }

    @classmethod
    def fts_type_title(cls, request: LandsgemeindeRequest) -> str:  # type: ignore[override]
        from onegov.landsgemeinde.layouts import DefaultLayout
        return DefaultLayout(None, request).assembly_type_plural

    @property
    def fts_last_change(self) -> datetime:
        return standardize_date(as_datetime(self.date), 'Europe/Zurich')

    @property
    def fts_suggestion(self) -> tuple[str, ...]:
        return (
            str(self.date.year),
            # FIXME: This is quite the hack and probably won't result
            #        in actually good results, we would need to insert
            #        this suggestion as part of the search terms, but
            #        even then we would probably want to localize this
            #        and make it depend on the assembly_title setting.
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

    filenames = ['memorial_pdf', 'memorial_2_pdf', 'memorial_supplement_pdf',
                 'protocol_pdf', 'audio_mp3', 'audio_zip']

    @property
    def more_files(self) -> list[File]:
        files = self.files
        return [file for file in files if file.name not in self.filenames]

    @more_files.setter
    def more_files(self, value: list[File]) -> None:
        existing_files = {
            file.name: file for file in self.files
            if file.name not in self.filenames
        }

        for file in existing_files.values():
            if file not in value:
                self.files.remove(file)

        for file in value:
            if file.name not in existing_files:
                self.files.append(file)

    @observes('files', 'date')
    def update_assembly_date(self, files: list[File], date: date_t) -> None:
        if not files or date is None:
            # nothing to do
            return

        for file in files:
            if file.meta.get('assembly_date') != date:
                file.meta['assembly_date'] = date
                flag_modified(file, 'meta')
