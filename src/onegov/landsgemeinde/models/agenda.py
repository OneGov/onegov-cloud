from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
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
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


STATES = {
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
    memorial_pdf = NamedFile(cls=LandsgemeindeFile)

    #: The page number on which the agenda item can be found
    memorial_page = content_property()

    #: The overview (text) over the agenda item
    overview = content_property()

    #: The main content (text) of the agenda item
    text = content_property()

    #: The resolution (text) of the agenda item
    resolution = content_property()

    #: The resolution (tags) of the agenda item
    resolution_tags = content_property()

    #: The video timestamp of this agenda item
    video_timestamp = content_property()

    #: An agenda item contains n vota
    vota = relationship(
        Votum,
        cascade='all, delete-orphan',
        backref=backref('agenda_item'),
        order_by='Votum.number',
    )

    #: The local start time
    start_time = Column(Time)

    def start(self):
        self.start_time = to_timezone(utcnow(), 'Europe/Zurich').time()

    #: The timestamp of the last modification
    last_modified = Column(UTCDateTime)

    def stamp(self):
        self.last_modified = self.timestamp()

    @property
    def date(self):
        return self.assembly.date

    @property
    def title_parts(self):
        lines = (self.title or '').splitlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line]
        return lines

    @property
    def video_url(self):
        video_url = self.assembly.video_url
        if video_url:
            return f'{video_url}#t={self.video_timestamp}'
