from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.landsgemeinde import _
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import Time
from uuid import uuid4


STATES = {
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class AgendaItem(Base, ContentMixin, TimestampMixin, AssociatedFiles):

    __tablename__ = 'landsgemeinde_agenda_items'

    #: the internal id of the agenda item
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the external id of the agenda item
    number = Column(Integer, nullable=False)

    #: the state of the agenda item
    state = Column(
        Enum(*STATES.keys(), name='agenda_item_state'),
        nullable=False
    )

    #: True if the item has been declared irrelevant
    irrelevant = Column(Boolean, nullable=False, default=False)

    #: True if the item has been tacitly accepted
    tacitly_accepted = Column(Boolean, nullable=False, default=False)

    #: the assembly this agenda item belongs to
    assembly_id = Column(
        UUID,
        ForeignKey(
            'landsgemeinde_assemblies.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    #: Title of the agenda item (not translated)
    title = Column(Text, nullable=False, default=lambda: '')

    #: The memorial of the assembly
    memorial_pdf = NamedFile()

    #: The overview (text) over the agenda item
    overview = content_property()

    #: The main content (text) of the agenda item
    text = content_property()

    #: The resolution (text) of the agenda item
    resolution = content_property()

    #: The resolution (tags) of the agenda item
    resolution_tags = content_property()

    @property
    def date(self):
        return self.assembly.date

    @property
    def title_parts(self):
        lines = (self.title or '').splitlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line]
        return lines

    #: Start of the agenda item (localized to Europe/Zurich)
    start = Column(Time, nullable=True)
