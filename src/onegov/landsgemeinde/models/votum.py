from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
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
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date as date_t
    from onegov.landsgemeinde.models import AgendaItem
    from translationstring import TranslationString
    from typing_extensions import TypeAlias

    VotumState: TypeAlias = Literal['scheduled', 'ongoing', 'completed']


STATES: dict['VotumState', 'TranslationString'] = {
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
    def es_suggestion(self) -> tuple[str, ...]:
        return ()

    #: the internal id of the votum
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the state of the votum
    state: 'Column[VotumState]' = Column(
        Enum(*STATES.keys(), name='votum_item_state'),  # type:ignore[arg-type]
        nullable=False
    )

    #: the external id of the agenda item
    number: 'Column[int]' = Column(Integer, nullable=False)

    #: The main text of the votum
    text: dict_property[str | None] = content_property()

    #: Motion of the votum
    motion: dict_property[str | None] = content_property()

    #: Statement of reasons of the votum
    statement_of_reasons: dict_property[str | None] = content_property()

    #: The name of the person
    person_name: 'Column[str | None]' = Column(Text, nullable=True)

    #: The function of the person
    person_function: 'Column[str | None]' = Column(Text, nullable=True)

    #: The place of the person
    person_place: 'Column[str | None]' = Column(Text, nullable=True)

    #: The political affiliation of the person (party or parliamentary group)
    person_political_affiliation: 'Column[str | None]' = Column(
        Text,
        nullable=True
    )

    #: A picture of the person
    person_picture: 'Column[str | None]' = Column(Text, nullable=True)

    #: The video timestamp of this agenda item
    video_timestamp: dict_property[str | None] = content_property()

    #: the agenda this votum belongs to
    agenda_item_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(
            'landsgemeinde_agenda_items.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    agenda_item: 'relationship[AgendaItem]' = relationship(
        'AgendaItem',
        back_populates='vota',
    )

    @property
    def date(self) -> 'date_t':
        return self.agenda_item.date

    @property
    def agenda_item_number(self) -> int:
        return self.agenda_item.number

    @property
    def video_url(self) -> str | None:
        video_url = self.agenda_item.assembly.video_url
        if video_url:
            return f'{video_url}#t={self.video_timestamp}'
        return None

    @property
    def person_details(self) -> str:
        details = (
            self.person_function,
            self.person_political_affiliation,
            self.person_place
        )
        return ', '.join(d for d in details if d)
