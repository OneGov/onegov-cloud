from uuid import uuid4

from onegov.search import ORMSearchable
from libres.db.models.timestamp import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Boolean, Float
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import UUID
from onegov.translator_directory.constants import ADMISSIONS, GENDERS
from onegov.translator_directory.models.certificate import \
    certificate_association_table
from onegov.translator_directory.models.documents import CertificateFile, \
    ApplicationFile, ClarificationFile, ConfirmationFile, ComplaintFile, \
    CorrespondenceFile, MiscFile
from onegov.translator_directory.models.language import \
    mother_tongue_association_table, spoken_association_table, \
    written_association_table


class DocumentsMixin(object):
    # Associated files
    certificates = associated(CertificateFile, 'certificates', 'one-to-many')
    applications = associated(ApplicationFile, 'applications', 'one-to-many')
    clarifications = associated(
        ClarificationFile, 'clarifications', 'one-to-many')
    confirmations = associated(
        ConfirmationFile, 'confirmations', 'one-to-many')
    complaints = associated(ComplaintFile, 'complaints', 'one-to-many')
    correspondences = associated(
        CorrespondenceFile, 'correspondences', 'one-to-many')
    other_files = associated(MiscFile, 'other_files', 'one-to-many')


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


class Translator(Base, TimestampMixin, DocumentsMixin):

    __tablename__ = 'translators'

    id = Column(UUID, primary_key=True, default=uuid4)

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

    email = Column(Text)

    tel_mobile = Column(Text,)
    tel_private = Column(Text)
    tel_office = Column(Text)

    availability = Column(Text)

    confirm_name_reveal = Column(Boolean, default=False)

    # The translator applies to be in the directory and gets a decision
    date_of_application = Column(Date)
    date_of_decision = Column(Date)

    # Language Information
    mother_tongues = relationship(
        "Language",
        secondary=mother_tongue_association_table,
        backref='mother_tongues'
    )

    spoken_languages = relationship(
        "Language", secondary=spoken_association_table, backref="speakers"
    )
    written_languages = relationship(
        "Language", secondary=written_association_table, backref='writers')

    # Nachweis der Voraussetzungen
    proof_of_preconditions = Column(Text)

    # Referenzen Behörden
    agency_references = Column(Text)

    # Ausbildung Dolmetscher
    education_as_interpreter = Column(Boolean, default=False, nullable=False)

    certificates = relationship(
        'LanguageCertificate',
        secondary=certificate_association_table,
        backref='owners')

    # Bemerkungen
    comments = Column(Text)

    # field for hiding to users except admins
    for_admins_only = Column(Boolean, default=False, nullable=False)

    # the below might never be used, but we import it if customer wants them
    occupation = Column(Text)
    other_certificates = Column(Text)

    # Besondere Hinweise Einsatzmöglichkeiten
    operation_comments = Column(Text)

    @property
    def title(self):
        return f'{self.last_name}, {self.first_name}'
