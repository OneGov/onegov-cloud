from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.file import NamedFile
from onegov.landsgemeinde import _
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


class Votum(Base, ContentMixin, TimestampMixin, AssociatedFiles):

    __tablename__ = 'landsgemeinde_vota'

    #: the internal id of the votum
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the state of the votum
    state = Column(
        Enum(*STATES.keys(), name='votum_item_state'),
        nullable=False
    )

    #: the external id of the agenda item
    number = Column(Integer, nullable=False)

    #: Motion of the votum
    motion = content_property()

    #: Statement of reasons of the votum
    statement_of_reasons = content_property()

    #: Start of the votum (localized to Europe/Zurich)
    start = Column(Time, nullable=True)

    #: The name of the person
    person_name = Column(Text, nullable=True)

    #: The function of the person
    person_function = Column(Text, nullable=True)

    #: The place of the person
    person_place = Column(Text, nullable=True)

    #: The political affiliation of the person (party or parliamentary group)
    person_political_affiliation = Column(Text, nullable=True)

    #: A picture of the person
    person_picture = NamedFile()

    #: the agenda this votum belongs to
    agenda_item_id = Column(
        UUID,
        ForeignKey(
            'landsgemeinde_agenda_items.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    @property
    def date(self):
        return self.agenda_item.date

    @property
    def agenda_item_number(self):
        return self.agenda_item.number
