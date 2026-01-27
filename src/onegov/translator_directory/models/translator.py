from __future__ import annotations

from uuid import uuid4

from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Boolean, Float
from sqlalchemy.orm import backref, relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import (ContentMixin, dict_property,
                                    meta_property, content_property)
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.gis import CoordinatesMixin
from onegov.search import ORMSearchable
from onegov.translator_directory.constants import ADMISSIONS, GENDERS
from onegov.translator_directory.i18n import _
from onegov.translator_directory.models.certificate import (
    certificate_association_table
)
from onegov.translator_directory.models.language import (
    mother_tongue_association_table, spoken_association_table,
    written_association_table, monitoring_association_table
)


from typing import Literal, TYPE_CHECKING

from ..utils import country_code_to_name

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence
    from datetime import date
    from onegov.user import User
    from typing import TypeAlias

    from .certificate import LanguageCertificate
    from .language import Language
    from .time_report import TranslatorTimeReport

    TranslatorState: TypeAlias = Literal['proposed', 'published']
    AdmissionState: TypeAlias = Literal[
        'uncertified', 'in_progress', 'certified'
    ]
    Gender: TypeAlias = Literal['M', 'F', 'N']
    InterpretingType: TypeAlias = Literal[
        'simultaneous', 'consecutive', 'negotiation', 'whisper'
    ]


class Translator(Base, TimestampMixin, AssociatedFiles, ContentMixin,
                 CoordinatesMixin, ORMSearchable):

    __tablename__ = 'translators'

    fts_type_title = _('Translators')
    fts_public = False
    fts_title_property = '_title'
    fts_properties = {
        # TODO: We may get better results if we use the fullname
        #       although we may have to supply the fullname without
        #       capitalization of the last name.
        'last_name': {'type': 'text', 'weight': 'A'},
        'first_name': {'type': 'text', 'weight': 'A'},
        'email': {'type': 'text', 'weight': 'A'}
    }

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    state: Column[TranslatorState] = Column(
        Enum(  # type:ignore[arg-type]
            'proposed',
            'published',
            name='translator_state'
        ),
        nullable=False,
        default='published'
    )

    first_name: Column[str] = Column(Text, nullable=False)
    last_name: Column[str] = Column(Text, nullable=False)

    # Personal-Nr.
    pers_id: Column[int | None] = Column(Integer)

    # Zulassung / admission
    admission: Column[AdmissionState] = Column(
        Enum(*ADMISSIONS, name='admission_state'),  # type:ignore[arg-type]
        nullable=False,
        default='uncertified'
    )

    # Quellensteuer
    withholding_tax: Column[bool] = Column(Boolean, default=False)

    # Selbständig
    self_employed: Column[bool] = Column(Boolean, default=False)

    gender: Column[Gender | None] = Column(
        Enum(*GENDERS, name='gender')  # type:ignore[arg-type]
    )
    date_of_birth: Column[date | None] = Column(Date)

    # Nationalitäten
    nationalities: dict_property[list[str] | None] = content_property()

    # Fields concerning address
    address: Column[str | None] = Column(Text)
    zip_code: Column[str | None] = Column(Text)
    city: Column[str | None] = Column(Text)

    # Heimatort
    hometown: Column[str | None] = Column(Text)

    # distance calculated from address to a fixed point via api, im km
    drive_distance: Column[float | None] = Column(
        Float(precision=2)  # type:ignore[arg-type]
    )

    # AHV-Nr.
    social_sec_number = Column(Text)

    # Bank information
    bank_name: Column[str | None] = Column(Text)
    bank_address: Column[str | None] = Column(Text)
    account_owner: Column[str | None] = Column(Text)
    iban: Column[str | None] = Column(Text)

    email: Column[str | None] = Column(Text, unique=True)

    # the user account related to this translator
    user: relationship[User] = relationship(
        'User',
        primaryjoin='foreign(Translator.email) == User.username',
        uselist=False,
        backref=backref('translator', uselist=False, passive_deletes='all')
    )

    tel_mobile: Column[str | None] = Column(Text)
    tel_private: Column[str | None] = Column(Text)
    tel_office: Column[str | None] = Column(Text)

    availability: Column[str | None] = Column(Text)

    confirm_name_reveal: Column[bool | None] = Column(Boolean, default=False)

    # The translator applies to be in the directory and gets a decision
    date_of_application: Column[date | None] = Column(Date)
    date_of_decision: Column[date | None] = Column(Date)

    # Language Information
    mother_tongues: relationship[list[Language]] = relationship(
        'Language',
        secondary=mother_tongue_association_table,
        back_populates='mother_tongues'
    )
    # Arbeitssprache - Wort
    spoken_languages: relationship[list[Language]] = relationship(
        'Language',
        secondary=spoken_association_table,
        back_populates='speakers'
    )
    # Arbeitssprache - Schrift
    written_languages: relationship[list[Language]] = relationship(
        'Language',
        secondary=written_association_table,
        back_populates='writers'
    )
    # Arbeitssprache - Kommunikationsüberwachung
    monitoring_languages: relationship[list[Language]] = relationship(
        'Language',
        secondary=monitoring_association_table,
        back_populates='monitors'
    )

    # Nachweis der Voraussetzungen
    proof_of_preconditions: Column[str | None] = Column(Text)

    # Referenzen Behörden
    agency_references: Column[str | None] = Column(Text)

    # Ausbildung Dolmetscher
    education_as_interpreter: Column[bool] = Column(
        Boolean,
        default=False,
        nullable=False
    )

    certificates: relationship[list[LanguageCertificate]] = relationship(
        'LanguageCertificate',
        secondary=certificate_association_table,
        back_populates='owners')

    # Time reports for this translator
    time_reports: relationship[list[TranslatorTimeReport]] = relationship(
        'TranslatorTimeReport',
        back_populates='translator',
        order_by='TranslatorTimeReport.assignment_date.desc()',
        cascade='all, delete-orphan',
    )

    # Bemerkungen
    comments: Column[str | None] = Column(Text)

    # field for hiding to users except admins
    for_admins_only: Column[bool] = Column(
        Boolean,
        default=False,
        nullable=False
    )

    # the below might never be used, but we import it if customer wants them
    profession: Column[str | None] = Column(Text)
    occupation: Column[str | None] = Column(Text)
    other_certificates: Column[str | None] = Column(Text)

    # Besondere Hinweise Einsatzmöglichkeiten
    operation_comments: Column[str | None] = Column(Text)

    # List of types of interpreting the interpreter can do
    expertise_interpreting_types: dict_property[Sequence[InterpretingType]] = (
        meta_property(default=tuple)
    )

    # List of types of professional guilds
    expertise_professional_guilds: dict_property[Sequence[str]] = (
        meta_property(default=tuple)
    )
    expertise_professional_guilds_other: dict_property[Sequence[str]] = (
        meta_property(default=tuple)
    )

    @property
    def expertise_professional_guilds_all(self) -> Sequence[str]:
        return (
            tuple(self.expertise_professional_guilds or ())
            + tuple(self.expertise_professional_guilds_other or ())
        )

    # If entry was imported, for the form and the expertise fields
    imported: Column[bool] = Column(Boolean, default=False, nullable=False)

    @property
    def _title(self) -> str:
        """ The title used for searching. """
        return f'{self.first_name} {self.last_name}'

    @property
    def title(self) -> str:
        """ Returns title with lastname in uppercase. """
        return f'{self.last_name.upper()}, {self.first_name}'

    @property
    def lead(self) -> str:
        return ', '.join({
            *(la.name for la in self.written_languages or []),
            *(la.name for la in self.spoken_languages or [])
        })

    @property
    def full_name(self) -> str:
        """ Returns the full name with lastname in uppercase. """
        return f'{self.first_name} {self.last_name.upper()}'

    @property
    def unique_categories(self) -> list[str]:
        return sorted({f.note for f in self.files if f.note is not None})

    def nationalities_as_text(
        self, locale: str,
        country_codes: list[str] | None = None
    ) -> str:
        """
        Returns the translators nationalities as text, translated to the given
        locale.
        If `country_codes` e.g. ['CH'] is given, the given codes are
        translated to country names instead.

        """
        mapping = country_code_to_name(locale)
        if country_codes:
            return ', '.join(mapping.get(code, code) for code in country_codes)

        return ', '.join(
            mapping.get(nat, nat)
            for nat in self.nationalities) if self.nationalities else '-'
