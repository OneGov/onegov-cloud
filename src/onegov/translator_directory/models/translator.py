from uuid import uuid4

from libres.db.models.timestamp import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Boolean, Float
from sqlalchemy.orm import backref, relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, dict_property, meta_property
from onegov.core.orm.types import UUID
from onegov.file import AssociatedFiles
from onegov.gis import CoordinatesMixin
from onegov.search import ORMSearchable
from onegov.translator_directory.constants import ADMISSIONS, GENDERS
from onegov.translator_directory.models.certificate import (
    certificate_association_table
)
from onegov.translator_directory.models.language import (
    mother_tongue_association_table, spoken_association_table,
    written_association_table, monitoring_association_table
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.user import User
    from .certificate import LanguageCertificate
    from .language import Language


class ESMixin(ORMSearchable):

    es_properties = {
        'last_name': {'type': 'text'},
        'first_name': {'type': 'text'},
        'email': {'type': 'text'}
    }

    es_public = False

    @property
    def lead(self):
        return ', '.join({
            *(la.name for la in self.written_languages or []),
            *(la.name for la in self.spoken_languages or [])
        })


class Translator(Base, TimestampMixin, AssociatedFiles, ContentMixin,
                 CoordinatesMixin, ESMixin):

    __tablename__ = 'translators'

    id = Column(UUID, primary_key=True, default=uuid4)

    state = Column(
        Enum(
            'proposed',
            'published',
            name='translator_state'
        ),
        nullable=False,
        default='published'
    )

    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)

    # Personal-Nr.
    pers_id = Column(Integer)

    # Zulassung / admission
    admission = Column(
        Enum(*ADMISSIONS, name='admission_state'),
        nullable=False,
        default='uncertified'
    )

    # Quellensteuer
    withholding_tax = Column(Boolean, default=False)

    # Selbständig
    self_employed = Column(Boolean, default=False)

    gender = Column(Enum(*GENDERS, name='gender'))
    date_of_birth = Column(Date)
    nationality = Column(Text)

    # Fields concerning address
    address = Column(Text)
    zip_code = Column(Text)
    city = Column(Text)

    # distance calculated from address to a fix point via api, im km
    drive_distance = Column(Float(precision=2))

    # AHV-Nr.
    social_sec_number = Column(Text)

    # Bank information
    bank_name = Column(Text)
    bank_address = Column(Text)
    account_owner = Column(Text)
    iban = Column(Text)

    email = Column(Text, unique=True)

    # the user account related to this translator
    user: 'relationship[User]' = relationship(
        'User',
        primaryjoin='foreign(Translator.email) == User.username',
        uselist=False,
        backref=backref('translator', uselist=False, passive_deletes='all')
    )

    tel_mobile = Column(Text,)
    tel_private = Column(Text)
    tel_office = Column(Text)

    availability = Column(Text)

    confirm_name_reveal = Column(Boolean, default=False)

    # The translator applies to be in the directory and gets a decision
    date_of_application = Column(Date)
    date_of_decision = Column(Date)

    # Language Information
    mother_tongues: 'relationship[list[Language]]' = relationship(
        "Language",
        secondary=mother_tongue_association_table,
        backref='mother_tongues'
    )

    # Arbeitssprache - Wort
    spoken_languages: 'relationship[list[Language]]' = relationship(
        "Language", secondary=spoken_association_table, backref="speakers"
    )
    # Arbeitssprache - Schrift
    written_languages: 'relationship[list[Language]]' = relationship(
        "Language", secondary=written_association_table, backref='writers')

    # Arbeitssprache - Kommunikationsüberwachung
    monitoring_languages: 'relationship[list[Language]]' = relationship(
        "Language", secondary=monitoring_association_table, backref='monitors')

    # Nachweis der Voraussetzungen
    proof_of_preconditions = Column(Text)

    # Referenzen Behörden
    agency_references = Column(Text)

    # Ausbildung Dolmetscher
    education_as_interpreter = Column(Boolean, default=False, nullable=False)

    certificates: 'relationship[list[LanguageCertificate]]' = relationship(
        'LanguageCertificate',
        secondary=certificate_association_table,
        backref='owners')

    # Bemerkungen
    comments = Column(Text)

    # field for hiding to users except admins
    for_admins_only = Column(Boolean, default=False, nullable=False)

    # the below might never be used, but we import it if customer wants them
    profession = Column(Text)
    occupation = Column(Text)
    other_certificates = Column(Text)

    # Besondere Hinweise Einsatzmöglichkeiten
    operation_comments = Column(Text)

    # List of types of interpreting the interpreter can do
    expertise_interpreting_types: 'dict_property[Sequence[str]]'
    expertise_interpreting_types = meta_property(default=tuple)

    # List of types of professional guilds
    expertise_professional_guilds: 'dict_property[Sequence[str]]'
    expertise_professional_guilds = meta_property(default=tuple)
    expertise_professional_guilds_other: 'dict_property[Sequence[str]]'
    expertise_professional_guilds_other = meta_property(default=tuple)

    @property
    def expertise_professional_guilds_all(self):
        return (
            tuple(self.expertise_professional_guilds or ())
            + tuple(self.expertise_professional_guilds_other or ())
        )

    # If entry was imported, for the form and the expertise fields
    imported = Column(Boolean, default=False, nullable=False)

    @property
    def title(self):
        return f'{self.last_name}, {self.first_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def unique_categories(self):
        return sorted({f.note for f in self.files})
