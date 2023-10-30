from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.landsgemeinde import _
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from uuid import uuid4


STATES = {
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class Votum(
    Base, ContentMixin, TimestampMixin, AssociatedFiles, ORMSearchable
):

    __tablename__ = 'landsgemeinde_vota'

    es_public = True
    es_properties = {
        'text': {'type': 'localized_html'},
        'motion': {'type': 'localized_html'},
        'statement_of_reasons': {'type': 'localized_html'},
        'person_name': {'type': 'text'},
        'person_function': {'type': 'text'},
        'person_place': {'type': 'text'},
        'person_political_affiliation': {'type': 'text'},
    }

    @property
    def es_suggestion(self):
        return ()

    #: the internal id of the votum
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the state of the votum
    state = Column(
        Enum(*STATES.keys(), name='votum_item_state'),
        nullable=False
    )

    #: the external id of the agenda item
    number = Column(Integer, nullable=False)

    #: The main text of the votum
    text = content_property()

    #: Motion of the votum
    motion = content_property()

    #: Statement of reasons of the votum
    statement_of_reasons = content_property()

    #: The name of the person
    person_name = Column(Text, nullable=True)

    #: The function of the person
    person_function = Column(Text, nullable=True)

    #: The place of the person
    person_place = Column(Text, nullable=True)

    #: The political affiliation of the person (party or parliamentary group)
    person_political_affiliation = Column(Text, nullable=True)

    #: A picture of the person
    person_picture = Column(Text, nullable=True)

    #: The video timestamp of this agenda item
    video_timestamp = content_property()

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

    @property
    def video_url(self):
        video_url = self.agenda_item.assembly.video_url
        if video_url:
            return f'{video_url}#t={self.video_timestamp}'

    @property
    def person_details(self):
        details = (
            self.person_function,
            self.person_political_affiliation,
            self.person_place
        )
        return ', '.join(d for d in details if d)
