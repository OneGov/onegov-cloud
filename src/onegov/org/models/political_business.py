from __future__ import annotations

from sqlalchemy import Column, Date, Enum, ForeignKey, Text
from sqlalchemy.orm import RelationshipProperty, relationship
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from onegov.org import _
from onegov.org.models.extensions import PoliticalBusinessParticipationExtension
from onegov.search import ORMSearchable
from onegov.org.models import Meeting

from typing import TYPE_CHECKING, TypeAlias, Literal

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from onegov.org.models import MeetingItem
    from onegov.org.models import RISParliamentarian


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
        'interpellation',  # Interpellation
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
        'abgeschrieben',
        'beantwortet',
        'erheblich_erklaert',
        'erledigt',
        'nicht_erheblich_erklaert',
        'nicht_zustandegekommen',
        'pendent_exekutive',
        'pendent_legislative',
        'rueckzug',
        'umgewandelt',
        'zurueckgewiesen',
        'ueberwiesen',
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
    'interpellation': _('Interpellation'),
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
    'abgeschrieben': _('Abgeschrieben'),
    'beantwortet': _('Beantwortet'),
    'erheblich_erklaert': _('Erheblich erklärt'),
    'erledigt': _('Erledigt'),
    'nicht_erheblich_erklaert': _('Nicht erheblich erklärt'),
    'nicht_zustandegekommen': _('Nicht zustandegekommen'),
    'pendent_exekutive': _('Pendent Exekutive'),
    'pendent_legislative': _('Pendent Legislative'),
    'rueckzug': _('Rückzug'),
    'umgewandelt': _('Umgewandelt'),
    'zurueckgewiesen': _('Zurückgewiesen'),
    'ueberwiesen': _('Überwiesen'),
}


class PoliticalBusiness(
    # AccessLinkExtension,
    Base,
    ContentMixin,
    # GeneralFileLinkExtension,
    ORMSearchable,
    PoliticalBusinessParticipationExtension
):

    GERMAN_STATUS_NAME_TO_VALUE_MAP: dict[str, str] = {
        'Abgeschrieben': 'written_off',
        'Beantwortet': 'answered',
        'Erheblich erklärt': 'declared_significant',
        'Erledigt': 'completed',
        'Nicht erheblich erklärt': 'declared_insignificant',
        'Nicht zustandegekommen': 'not_realized',
        'Pendent Exekutive': 'pending_executive',
        'Pendent Legislative': 'pending_legislative',
        'Rückzug': 'withdrawn',
        'Umgewandelt': 'converted',
        'Zurückgewiesen': 'rejected',
        'Überwiesen': 'referred',
    }

    # Politisches Geschäft

    __tablename__ = 'par_political_businesses'

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

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
            name='par_political_business_type',
        ),
        nullable=False,
    )

    #: status of the political business
    status: Column[PoliticalBusinessStatus | None] = Column(
        Enum(
            *POLITICAL_BUSINESS_STATUS.keys(),  # type:ignore[arg-type]
            name='par_political_business_status',
        ),
        nullable=True,
    )

    #: entry date of political business
    entry_date: Column[date | None] = Column(Date, nullable=True)

    #: may have participants (Verfasser/Beteiligte) depending on the type
    participants = relationship(
        'PoliticalBusinessParticipation',
        back_populates='political_business',
        lazy='joined',
        order_by='PoliticalBusinessParticipation.participant_type',
    )

    #: parliamentary group (Fraktion)
    # FIXME: make multiple groups possible
    parliamentary_group_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_parliamentary_groups.id'),
        nullable=True,
    )

    #: The meetings this agenda item was discussed in
    meetings: RelationshipProperty['Meeting'] = relationship(
        'Meeting',
        back_populates='political_businesses',
        order_by=Meeting.start_datetime,
        lazy='joined',
    )
    meeting_items: relationship[list['MeetingItem']] = relationship(
        'MeetingItem',
        back_populates='political_business'
    )

    def __repr__(self) -> str:
        return (f'<Political Business {self.number}, '
                f'{self.title}, {self.political_business_type}>')


class RISPoliticalBusiness(PoliticalBusiness):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_political_business',
    }

    es_type_name = 'ris_political_business'


class PoliticalBusinessParticipation(Base, ContentMixin):
    """ A participant of a political business, e.g. a parliamentarian. """

    __tablename__ = 'par_political_business_participants'

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4,
    )

    #: The id of the political business
    political_business_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_political_businesses.id'),
        nullable=False,
    )

    #: The id of the parliamentarian
    parliamentarian_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_parliamentarians.id'),
        nullable=False,
    )

    #: the role of the parliamentarian in the political business
    participant_type: Column[str | None] = Column(
        Text,
        nullable=True,
        default=None
    )

    #: the related political business
    political_business: RelationshipProperty[PoliticalBusiness]
    political_business = relationship(
        'PoliticalBusiness',
        back_populates='participants',
    )

    #: the related parliamentarian
    parliamentarian: RelationshipProperty[RISParliamentarian] = relationship(
        'RISParliamentarian',
        back_populates='political_businesses',
    )

    def __repr__(self) -> str:
        return (f'<Political Business Participation {self.parliamentarian.title}, '
                f'{self.political_business.title}, {self.participant_type}>')


class RISPoliticalBusinessParticipation(
    PoliticalBusinessParticipation
):

    __mapper_args__ = {
        'polymorphic_identity': 'ris_political_business_participation',
    }

    es_type_name = 'ris_political_business_participation'
