from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.file import AssociatedFiles
from onegov.landsgemeinde import _
from onegov.landsgemeinde.models.mixins import TimestampedVideoMixin
from onegov.landsgemeinde.observer import observes
from onegov.search import ORMSearchable
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.attributes import set_committed_value
from uuid import uuid4
from uuid import UUID


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date as date_t
    from datetime import datetime
    from onegov.file import File
    from onegov.landsgemeinde.models import AgendaItem
    from onegov.landsgemeinde.models import Assembly
    from translationstring import TranslationString
    from typing import TypeAlias


VotumState: TypeAlias = Literal[
    'draft', 'scheduled', 'ongoing', 'completed'
]

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

    fts_type_title = _('Vota')
    fts_public = True
    fts_title_property = None
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
    def fts_last_change(self) -> datetime:
        self._fetch_if_necessary()
        return self.agenda_item.fts_last_change

    @property
    def fts_suggestion(self) -> tuple[str, ...]:
        return ()

    def _fetch_if_necessary(self) -> None:
        session = object_session(self)
        if session is None:
            return

        if self.agenda_item_id is not None and self.agenda_item is None:
            # retrieve the assembly
            from onegov.landsgemeinde.models import AgendaItem  # type: ignore[unreachable]
            set_committed_value(
                self,
                'agenda_item',
                session.get(AgendaItem, self.agenda_item_id)
            )

    #: the internal id of the votum
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the state of the votum
    state: Mapped[VotumState] = mapped_column(
        Enum(*STATES.keys(), name='votum_item_state')
    )

    #: the external id of the agenda item
    number: Mapped[int]

    #: The main text of the votum
    text = dict_markup_property('content')

    #: Motion of the votum
    motion = dict_markup_property('content')

    #: Statement of reasons of the votum
    statement_of_reasons = dict_markup_property('content')

    #: The name of the person
    person_name: Mapped[str | None]

    #: The function of the person
    person_function: Mapped[str | None]

    #: The place of the person
    person_place: Mapped[str | None]

    #: The political affiliation of the person (party or parliamentary group)
    person_political_affiliation: Mapped[str | None]

    #: A picture of the person
    person_picture: Mapped[str | None]

    #: the agenda this votum belongs to
    agenda_item_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            'landsgemeinde_agenda_items.id',
            onupdate='CASCADE',
            ondelete='CASCADE'
        )
    )

    agenda_item: Mapped[AgendaItem] = relationship(back_populates='vota')

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

    @observes('files', 'agenda_item.assembly.date')
    def update_assembly_date(self, files: list[File], date: date_t) -> None:
        # NOTE: Makes sure we will get reindexed, it doesn't really
        #       matter what we flag as modified, we just pick something.
        flag_modified(self, 'number')
        if not files or date is None:
            # nothing else to do
            return

        for file in files:
            if file.meta.get('assembly_date') != date:
                file.meta['assembly_date'] = date
                flag_modified(file, 'meta')
