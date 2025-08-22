from __future__ import annotations

from datetime import date
from sqlalchemy import and_, or_, func, case
from sqlalchemy import Column, Date, Enum, ForeignKey, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4

from onegov.core.collection import GenericCollection, Pagination
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import toggle
from onegov.file import MultiAssociatedFiles
from onegov.org import _
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.search import ORMSearchable

from typing import Literal, Self, TypeAlias, TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from collections.abc import Collection
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement

    from onegov.org.models import Meeting
    from onegov.org.models import MeetingItem
    from onegov.org.models import RISParliamentarian
    from onegov.org.models import RISParliamentaryGroup

PoliticalBusinessType: TypeAlias = Literal[
    'inquiry',  # Anfrage
    'report and proposal',  # Bericht und Antrag
    'urgent interpellation',  # Dringliche Interpellation
    'invitation',  # Einladung
    'interpellation',  # Interpellation
    'commission report',  # Kommissionsbericht
    'motion',  # Motion
    'postulate',  # Postulat
    'resolution',  # Resolution
    'election',  # Wahl
    'parliamentary statement',  # Parlamentarische Erklärung
    'miscellaneous',  # Verschiedenes
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
    'report and proposal': _('Report and Proposal'),
    'urgent interpellation': _('Urgent Interpellation'),
    'invitation': _('Invitation'),
    'interpellation': _('Interpellation'),
    'commission report': _('Commission Report'),
    'motion': _('Motion'),
    'postulate': _('Postulate'),
    'resolution': _('Resolution'),
    'election': _('Election'),
    'parliamentary statement': _('Parliamentary Statement'),
    'miscellaneous': _('Miscellaneous'),
}

# FIXME: i18n
POLITICAL_BUSINESS_STATUS: dict[PoliticalBusinessStatus, str] = {
    'abgeschrieben': 'Abgeschrieben',
    'beantwortet': 'Beantwortet',
    'erheblich_erklaert': 'Erheblich erklärt',
    'erledigt': 'Erledigt',
    'nicht_erheblich_erklaert': 'Nicht erheblich erklärt',
    'nicht_zustandegekommen': 'Nicht zustandegekommen',
    'pendent_exekutive': 'Pendent Exekutive',
    'pendent_legislative': 'Pendent Legislative',
    'rueckzug': 'Rückzug',
    'umgewandelt': 'Umgewandelt',
    'zurueckgewiesen': 'Zurückgewiesen',
    'ueberwiesen': 'Überwiesen',
}


class PoliticalBusiness(
    AccessExtension,
    MultiAssociatedFiles,
    Base,
    ContentMixin,
    GeneralFileLinkExtension,
    ORMSearchable
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

    es_type_name = 'ris_political_business'
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
    participants: relationship[list[PoliticalBusinessParticipation]]
    participants = relationship(
        'PoliticalBusinessParticipation',
        back_populates='political_business',
        lazy='joined',
        order_by='desc(PoliticalBusinessParticipation.participant_type)',
    )

    #: parliamentary group (Fraktion)
    # FIXME: make multiple groups possible
    parliamentary_group_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('par_parliamentary_groups.id'),
        nullable=True,
    )
    parliamentary_group: relationship[RISParliamentaryGroup | None]
    parliamentary_group = relationship(
        'RISParliamentaryGroup',
        back_populates='political_businesses'
    )

    #: The meetings this agenda item was discussed in
    meetings: relationship[Meeting] = relationship(
        'Meeting',
        back_populates='political_businesses',
        order_by='Meeting.start_datetime',
        lazy='joined',
    )
    meeting_items: relationship[list[MeetingItem]] = relationship(
        'MeetingItem',
        back_populates='political_business'
    )

    @hybrid_property
    def display_name(self) -> str:
        return f'{self.number} {self.title}' if self.number else self.title

    @display_name.expression  # type:ignore[no-redef]
    def display_name(cls) -> ColumnElement[str]:
        return func.concat(
            func.coalesce(cls.number, ''),
            case([
                (and_(cls.number.isnot(None), cls.number != ''), ' ')
            ], else_=''),
            cls.title
        )

    def __repr__(self) -> str:
        return (f'<Political Business {self.number}, '
                f'{self.title}, {self.political_business_type}>')


class PoliticalBusinessParticipation(Base, ContentMixin):
    """ A participant of a political business, e.g. a parliamentarian. """

    __tablename__ = 'par_political_business_participants'

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
    political_business: relationship[PoliticalBusiness]
    political_business = relationship(
        'PoliticalBusiness',
        back_populates='participants',
    )

    #: the related parliamentarian
    parliamentarian: relationship[RISParliamentarian] = relationship(
        'RISParliamentarian',
        back_populates='political_businesses',
    )

    def __repr__(self) -> str:
        return (f'<Political Business Participation '
                f'{self.parliamentarian.title}, '
                f'{self.political_business.title}, '
                f'{self.participant_type}>')


class PoliticalBusinessCollection(
    GenericCollection[PoliticalBusiness],
    Pagination[PoliticalBusiness]
):

    def __init__(
        self,
        session: Session,
        page: int = 0,
        status: Collection[PoliticalBusinessStatus] | None = None,
        types: Collection[PoliticalBusinessType] | None = None,
        years: Collection[int] | None = None,
    ) -> None:
        super().__init__(session)
        self.page = page
        self.status = set(status) if status else set()
        self.types = set(types) if types else set()
        self.years = set(years) if years else set()
        self.batch_size = 20

    @property
    def model_class(self) -> type[PoliticalBusiness]:
        return PoliticalBusiness

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
        )

    def query(self) -> Query[PoliticalBusiness]:
        query = super().query()

        if self.types:
            query = query.filter(
                PoliticalBusiness.political_business_type.in_(self.types)
            )

        if self.status:
            query = query.filter(
                PoliticalBusiness.status.in_(self.status)
            )

        if self.years:
            query = query.filter(
                or_(*[
                    and_(
                        PoliticalBusiness.entry_date.isnot(None),
                        PoliticalBusiness.entry_date >= date(year, 1, 1),
                        PoliticalBusiness.entry_date < date(year + 1, 1, 1),
                    )
                    for year in self.years
                ])
            )

        return query.order_by(self.model_class.entry_date.desc())

    def query_all(self) -> Query[PoliticalBusiness]:
        """
        Returns a query for all political businesses, ignoring the page,
        status, types, and years filters.
        """
        return super().query().order_by(self.model_class.entry_date.desc())

    def subset(self) -> Query[PoliticalBusiness]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index,
            status=self.status,
            types=self.types,
            years=self.years,
        )

    @property
    def page_index(self) -> int:
        return self.page

    def for_filter(
        self,
        status: PoliticalBusinessStatus | None = None,
        type: PoliticalBusinessType | None = None,
        year: int | None = None,
    ) -> Self:
        status_ = toggle(self.status, status)
        types = toggle(self.types, type)
        years = toggle(self.years, year)

        return self.__class__(
            self.session,
            page=0,
            status=status_,
            types=types,
            years=years,
        )

    def years_for_entries(self) -> list[int]:
        """ Returns a list of years for which there are entries in the db """

        years = self.query_all().with_entities(
            func.extract('year', PoliticalBusiness.entry_date).label('year')
        ).filter(
            PoliticalBusiness.entry_date.isnot(None)
        ).distinct().order_by(
            PoliticalBusiness.entry_date.desc()
        )

        # convert to a list of integers, remove duplicates, and sort
        return sorted({int(year[0]) for year in years}, reverse=True)

    def by_display_name(self, display_name: str) -> PoliticalBusiness | None:
        """ Returns the given political business by display name or None. """
        return (
            self.query()
            .filter(PoliticalBusiness.display_name == display_name)  # type:ignore[comparison-overlap]
            .first()
        )


class PoliticalBusinessParticipationCollection(
    GenericCollection[PoliticalBusinessParticipation]
):

    def __init__(self, session: Session, active: bool | None = None):
        super().__init__(session)
        self.active = active

    @property
    def model_class(self) -> type[PoliticalBusinessParticipation]:
        return PoliticalBusinessParticipation

    def by_parliamentarian_id(
        self,
        parliamentarian_id: uuid.UUID
    ) -> Query[PoliticalBusinessParticipation]:
        query = super().query()
        return query.filter_by(parliamentarian_id=parliamentarian_id)
