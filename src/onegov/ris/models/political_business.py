from __future__ import annotations

from sqlalchemy import Column, Date, Enum, ForeignKey, Text
from sqlalchemy.orm import RelationshipProperty, relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from onegov.file import MultiAssociatedFiles
from onegov.ris import _
from onegov.ris.models.meeting import RISMeeting
from onegov.search import ORMSearchable


from typing import TYPE_CHECKING, TypeAlias, Literal

if TYPE_CHECKING:
    import uuid

    from datetime import date

    from onegov.ris.models import RISParliamentarian

    PoliticalBusinessType: TypeAlias = Literal[
        'inquiry',  # Anfrage
        'proposal',  # Antrag
        'mandate',  # Auftrag
        'report',   # Bericht
        'report and proposal',  # Bericht und Antrag
        'decision',  # Beschluss
        'message',   # Botschaft
        'urgent interpellation',  # Dringliche Interpellation
        'invitation',  # Einladung
        'interpelleation',  # Interpellation
        'commission report',  # Kommissionsbericht
        'communication',  # Mitteilung
        'motion',  # Motion
        'postulate',  # Postulat
        'resolution',  # Resolution
        'regulation',  # Verordnung
        'miscellaneous',  # Verschiedenes
        'elections'  # Wahlen
    ]

    PoliticalBusinessStatus: TypeAlias = Literal[
        'pending legislative',
        'pending executive',
        'substantial',
        'converted',
    ]

POLITICAL_BUSINESS_TYPE: dict[PoliticalBusinessType, str] = {
    'inquiry': _('Inquiry'),
    'proposal': _('Proposal'),
    'mandate': _('Mandate'),
    'report': _('Report'),
    'report and proposal': _('Report and Proposal'),
    'decision': _('Decision'),
    'message': _('Message'),
    'urgent interpellation': _('Urgent Interpellation'),
    'invitation': _('Invitation'),
    'interpelleation': _('Interpellation'),
    'commission report': _('Commission Report'),
    'communication': _('Communication'),
    'motion': _('Motion'),
    'postulate': _('Postulate'),
    'resolution': _('Resolution'),
    'regulation': _('Regulation'),
    'miscellaneous': _('Miscellaneous'),
    'elections': _('Elections'),
}

POLITICAL_BUSINESS_STATUS: dict[PoliticalBusinessStatus, str] = {
    'pending legislative': _('Pending legislative'),
    'pending executive': _('Pending executive'),
    'substantial': _('Substantial'),
    'converted': _('Converted'),
}


class RISPoliticalBusiness(Base, MultiAssociatedFiles, ContentMixin,
                           ORMSearchable):
    # Politisches Geschäft

    __tablename__ = 'ris_political_businesses'

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
        'number': {'type': 'text'}
    }

    @property
    def es_suggestion(self) -> str:
        return f'{self.title} {self.number}'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4,
    )

    #: The title of the agenda item
    title: Column[str] = Column(Text, nullable=False)

    #: number of the agenda item
    number: Column[str | None] = Column(Text, nullable=True)

    #: business type of the agenda item
    political_business_type: Column[PoliticalBusinessType] = Column(
        Enum(
            *POLITICAL_BUSINESS_TYPE.keys(),  # type:ignore[arg-type]
            name='ris_political_business_type',
        ),
        nullable=False,
    )

    #: status of the political business
    status: Column[PoliticalBusinessStatus | None] = Column(
        Enum(
            *POLITICAL_BUSINESS_STATUS.keys(),  # type:ignore[arg-type]
            name='ris_political_business_status',
        ),
        nullable=True,
    )

    #: entry date of political business
    entry_date: Column[date | None] = Column(Date, nullable=True)

    #: may have participants (Verfasser/Beteiligte) depending on the type
    participants = relationship(
        'RISPoliticalBusinessParticipation',
        back_populates='political_business',
        lazy='joined',
    )

    #: parliamentary group (Fraktion)
    parliamentary_group_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentary_groups.id'),
        nullable=True,
    )

    #: The meetings this agenda item was discussed in
    meetings: RelationshipProperty[RISMeeting] = relationship(
        'RISMeeting',
        back_populates='political_businesses',
        order_by=RISMeeting.start_datetime,
        lazy='joined',
    )

    def __repr__(self) -> str:
        return (f'<Political Business {self.number}, '
                f'{self.title}, {self.political_business_type}>')


class RISPoliticalBusinessParticipation(Base, ContentMixin, ORMSearchable):
    """ A participant of a political business, e.g. a parliamentarian. """

    __tablename__ = 'ris_political_business_participants'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4,
    )

    #: The id of the political business
    political_business_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_political_businesses.id'),
        nullable=False,
    )

    #: The id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('ris_parliamentarians.id'),
        nullable=False,
    )

    #:
    participant_type: Column[str] = Column(
        Enum('author', 'participant', name='ris_participant_type'),
        nullable=False,
    )

    #: the related political business
    political_business: RelationshipProperty[RISPoliticalBusiness]
    political_business = relationship(
        'RISPoliticalBusiness',
        back_populates='participants',
    )

    #: the related parliamentarian
    parliamentarian: RelationshipProperty[RISParliamentarian] = relationship(
        'RISParliamentarian',
        back_populates='political_businesses',
    )
