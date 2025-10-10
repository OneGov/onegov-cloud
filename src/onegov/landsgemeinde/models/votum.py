from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.landsgemeinde import _
from onegov.landsgemeinde.models.mixins import TimestampedVideoMixin
from onegov.search import ORMSearchable
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
    from onegov.landsgemeinde.models import AgendaItem
    from onegov.landsgemeinde.models import Assembly
    from translationstring import TranslationString
    from typing import Literal
    from typing import TypeAlias

    VotumState: TypeAlias = Literal[
        'draft', 'scheduled', 'ongoing', 'completed']


STATES: dict[VotumState, TranslationString] = {
    'draft': _('draft'),
    'scheduled': _('scheduled'),
    'ongoing': _('ongoing'),
    'completed': _('completed')
}


class Votum(
    Base, ContentMixin, TimestampMixin, AssociatedFiles, ORMSearchable,
    TimestampedVideoMixin
):

    __tablename__ = 'landsgemeinde_vota'

    fts_public = True
    fts_properties = {
        'text': {'type': 'localized', 'weight': 'A'},
        'motion': {'type': 'localized', 'weight': 'A'},
        'statement_of_reasons': {'type': 'localized', 'weight': 'C'},
        'person_name': {'type': 'text', 'weight': 'A'},
        'person_function': {'type': 'text', 'weight': 'B'},
        'person_place': {'type': 'text', 'weight': 'D'},
        'person_political_affiliation': {'type': 'text', 'weight': 'C'},
    }

    @property
    def fts_suggestion(self) -> tuple[str, ...]:
        return ()

    #: the internal id of the votum
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the state of the votum
    state: Column[VotumState] = Column(
        Enum(*STATES.keys(), name='votum_item_state'),  # type:ignore[arg-type]
        nullable=False
    )

    #: the external id of the agenda item
    number: Column[int] = Column(Integer, nullable=False)

    #: The main text of the votum
    text = dict_markup_property('content')

    #: Motion of the votum
    motion = dict_markup_property('content')

    #: Statement of reasons of the votum
    statement_of_reasons = dict_markup_property('content')

    #: The name of the person
    person_name: Column[str | None] = Column(Text, nullable=True)

    #: The function of the person
    person_function: Column[str | None] = Column(Text, nullable=True)

    #: The place of the person
    person_place: Column[str | None] = Column(Text, nullable=True)

    #: The political affiliation of the person (party or parliamentary group)
    person_political_affiliation: Column[str | None] = Column(
        Text,
        nullable=True
    )

    #: A picture of the person
    person_picture: Column[str | None] = Column(Text, nullable=True)

    #: the agenda this votum belongs to
    agenda_item_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(
            'landsgemeinde_agenda_items.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        ),
        nullable=False
    )

    agenda_item: relationship[AgendaItem] = relationship(
        'AgendaItem',
        back_populates='vota',
    )

    @property
    def date(self) -> date_t:
        return self.agenda_item.date

    @property
    def agenda_item_number(self) -> int:
        return self.agenda_item.number

    @property
    def assembly(self) -> Assembly:  # type:ignore[override]
        return self.agenda_item.assembly

    @property
    def person_details(self) -> str:
        details = (
            self.person_function,
            self.person_political_affiliation,
            self.person_place
        )
        return ', '.join(d for d in details if d)
