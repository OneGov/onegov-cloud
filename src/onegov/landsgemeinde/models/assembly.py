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
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .agenda import AgendaItem


STATES = {
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class Assembly(Base, ContentMixin, TimestampMixin, AssociatedFiles):

    __tablename__ = 'landsgemeinde_assemblies'

    #: Internal number of the event
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the state of the assembly
    state = Column(
        Enum(*STATES.keys(), name='assembly_state'),
        nullable=False
    )

    #: The date of the assembly
    date = Column(Date, nullable=False, unique=True)

    #: True if this is an extraordinary assembly
    extraordinary = Column(Boolean, nullable=False, default=False)

    #: the logo of the organisation
    video_url = Column(Text, nullable=True)

    #: The memorial of the assembly
    memorial_pdf = NamedFile()

    #: The protocol of the assembly
    protocol_pdf = NamedFile()

    #: The audio of the assembly as MP3
    audio_mp3 = NamedFile()

    #: The audio of the assembly as ZIP
    audio_zip = NamedFile()

    #: The overview (text) over the assembly
    overview = content_property()

    #: An assembly contains n agenda items
    agenda_items: 'relationship[list[AgendaItem]]' = relationship(
        'AgendaItem',
        cascade='all, delete-orphan',
        backref=backref('assembly'),
        lazy='dynamic',
        order_by='AgendaItem.number',
    )
