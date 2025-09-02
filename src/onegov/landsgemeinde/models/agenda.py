from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_markup_property
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
from onegov.landsgemeinde.models.mixins import TimestampedVideoMixin
from onegov.search import ORMSearchable
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t
    from onegov.landsgemeinde.models import Assembly
    from translationstring import TranslationString
    from typing import Literal
    from typing import TypeAlias

    AgendaItemState: TypeAlias = Literal[
        'draft', 'scheduled', 'ongoing', 'completed']


STATES: dict[AgendaItemState, TranslationString] = {
    'draft': _('draft'),
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class AgendaItem(
    Base, ContentMixin, TimestampMixin, AssociatedFiles, ORMSearchable,
    TimestampedVideoMixin
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
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the external id of the agenda item
    number: Column[int] = Column(Integer, nullable=False)

    #: the state of the agenda item
    state: Column[AgendaItemState] = Column(
        Enum(*STATES.keys(), name='agenda_item_state'),  # type:ignore
        nullable=False
    )

    #: True if the item has been declared irrelevant
    irrelevant: Column[bool] = Column(Boolean, nullable=False, default=False)

    #: True if the item has been tacitly accepted
    tacitly_accepted: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: the assembly this agenda item belongs to
    assembly_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(
            'landsgemeinde_assemblies.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    assembly: relationship[Assembly] = relationship(
        'Assembly',
        back_populates='agenda_items',
    )

    #: Title of the agenda item (not translated)
    title: Column[str] = Column(Text, nullable=False, default=lambda: '')

    #: The memorial of the assembly
    memorial_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The page number on which the agenda item can be found
    memorial_page: dict_property[int | None] = content_property()

    #: The overview (text) over the agenda item
    overview = dict_markup_property('content')

    #: The main content (text) of the agenda item
    text = dict_markup_property('content')

    #: The resolution (text) of the agenda item
    resolution = dict_markup_property('content')

    #: The resolution (tags) of the agenda item
    resolution_tags: dict_property[list[str] | None] = content_property()

    #: An agenda item contains n vota
    vota: relationship[list[Votum]] = relationship(
        Votum,
        cascade='all, delete-orphan',
        back_populates='agenda_item',
        order_by='Votum.number',
    )

    #: The timestamp of the last modification
    last_modified = Column(UTCDateTime)

    def stamp(self) -> None:
        self.last_modified = self.timestamp()

    @property
    def date(self) -> date_t:
        return self.assembly.date

    @property
    def title_parts(self) -> list[str]:
        return [
            stripped_line
            for line in (self.title or '').splitlines()
            if (stripped_line := line.strip())
        ]

    @property
    def more_files(self) -> list[LandsgemeindeFile]:
        files = self.files
        if self.memorial_pdf:
            return [
                file for file in files
                if file != self.memorial_pdf and isinstance(file,
                                                            LandsgemeindeFile)
            ]
        return []

    @more_files.setter
    def more_files(self, value: list[LandsgemeindeFile]) -> None:
        if self.memorial_pdf:
            self.files = value + [self.memorial_pdf]
        else:
            self.files = value  # type: ignore
