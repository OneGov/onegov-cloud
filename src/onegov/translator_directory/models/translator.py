from __future__ import annotations

from datetime import date
from uuid import uuid4, UUID

from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Enum, Float
from sqlalchemy.orm import backref, mapped_column, relationship, Mapped

from onegov.core.orm import Base
from onegov.core.orm.mixins import (ContentMixin, dict_property,
                                    meta_property, content_property)
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

from ..utils import country_code_to_name


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
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

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    state: Mapped[TranslatorState] = mapped_column(
        Enum(
            'proposed',
            'published',
            name='translator_state'
        ),
        default='published'
    )

    first_name: Mapped[str]
    last_name: Mapped[str]

    # Personal-Nr.
    pers_id: Mapped[int | None]

    # Vertragsnummer / AnsV-Nr. (Anstellungsverhältnis-Nr.)
    contract_number: Mapped[str | None]

    # Zulassung / admission
    admission: Mapped[AdmissionState] = mapped_column(
        Enum(*ADMISSIONS, name='admission_state'),
        default='uncertified'
    )

    # Quellensteuer
    # FIXME: These probably should've not been nullable
    withholding_tax: Mapped[bool] = mapped_column(nullable=True, default=False)

    # Selbständig
    # FIXME: These probably should've not been nullable
    self_employed: Mapped[bool] = mapped_column(nullable=True, default=False)

    gender: Mapped[Gender | None] = mapped_column(
        Enum(*GENDERS, name='gender')
    )
    date_of_birth: Mapped[date | None]

    # Nationalitäten
    nationalities: dict_property[list[str] | None] = content_property()

    # Fields concerning address
    address: Mapped[str | None]
    zip_code: Mapped[str | None]
    city: Mapped[str | None]

    # Heimatort
    hometown: Mapped[str | None]

    # distance calculated from address to a fixed point via api, im km
    drive_distance: Mapped[float | None] = mapped_column(
        Float(precision=2)
    )

    # AHV-Nr.
    social_sec_number: Mapped[str | None]

    # Bank information
    bank_name: Mapped[str | None]
    bank_address: Mapped[str | None]
    account_owner: Mapped[str | None]
    iban: Mapped[str | None]

    email: Mapped[str | None] = mapped_column(unique=True)

    # the user account related to this translator
    user: Mapped[User] = relationship(
        primaryjoin='foreign(Translator.email) == User.username',
        uselist=False,
        backref=backref('translator', uselist=False, passive_deletes='all')
    )

    tel_mobile: Mapped[str | None]
    tel_private: Mapped[str | None]
    tel_office: Mapped[str | None]

    availability: Mapped[str | None]

    confirm_name_reveal: Mapped[bool | None] = mapped_column(default=False)

    # The translator applies to be in the directory and gets a decision
    date_of_application: Mapped[date | None]
    date_of_decision: Mapped[date | None]

    # Language Information
    mother_tongues: Mapped[list[Language]] = relationship(
        secondary=mother_tongue_association_table,
        back_populates='mother_tongues'
    )
    # Arbeitssprache - Wort
    spoken_languages: Mapped[list[Language]] = relationship(
        secondary=spoken_association_table,
        back_populates='speakers'
    )
    # Arbeitssprache - Schrift
    written_languages: Mapped[list[Language]] = relationship(
        secondary=written_association_table,
        back_populates='writers'
    )
    # Arbeitssprache - Kommunikationsüberwachung
    monitoring_languages: Mapped[list[Language]] = relationship(
        secondary=monitoring_association_table,
        back_populates='monitors'
    )

    # Nachweis der Voraussetzungen
    proof_of_preconditions: Mapped[str | None]

    # Referenzen Behörden
    agency_references: Mapped[str | None]

    # Ausbildung Dolmetscher
    education_as_interpreter: Mapped[bool] = mapped_column(default=False)

    certificates: Mapped[list[LanguageCertificate]] = relationship(
        secondary=certificate_association_table,
        back_populates='owners'
    )

    # Time reports for this translator
    time_reports: Mapped[list[TranslatorTimeReport]] = relationship(
        back_populates='translator',
        order_by='TranslatorTimeReport.assignment_date.desc()',
        cascade='all, delete-orphan',
    )

    # Bemerkungen
    comments: Mapped[str | None]

    # field for hiding to users except admins
    for_admins_only: Mapped[bool] = mapped_column(default=False)

    # the below might never be used, but we import it if customer wants them
    profession: Mapped[str | None]
    occupation: Mapped[str | None]
    other_certificates: Mapped[str | None]

    # Besondere Hinweise Einsatzmöglichkeiten
    operation_comments: Mapped[str | None]

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
    imported: Mapped[bool] = mapped_column(default=False)

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
