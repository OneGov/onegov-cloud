from uuid import uuid4

from onegov.core.orm.mixins import ContentMixin
from onegov.gis import CoordinatesMixin
from onegov.search import ORMSearchable
from onegov.translator_directory import _
from libres.db.models.timestamp import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Table, ForeignKey, \
    Boolean, Index, Float
from sqlalchemy.orm import relationship, object_session

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import UUID
from onegov.translator_directory.models.documents import CertificateFile, \
    ApplicationFile, ClarificationFile, ConfirmationFile, ComplaintFile, \
    CorrespondenceFile, MiscFile

ADMISSIONS = ('uncertified', 'in_progress', 'certified')
ADMISSIONS_DESC = (_('uncertified'), _('in progress'), _('certified'))
GENDERS = ('M', 'F', 'N')
GENDERS_DESC = (_('masculin'), _('feminin'), 'neutral')
CERTIFICATES = ('ZHAW', 'OGZH')


class Language(Base):

    __tablename__ = 'languages'

    __table_args__ = (
        Index('unique_name', 'name', unique=True),
    )

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)

    @property
    def speakers_count(self):
        session = object_session(self)
        return session.query(
            spoken_association_table).filter_by(lang_id=self.id).count()

    @property
    def writers_count(self):
        session = object_session(self)
        return session.query(
            written_association_table).filter_by(lang_id=self.id).count()

    @property
    def native_speakers_count(self):
        """Having it as mother tongue..."""
        session = object_session(self)
        return session.query(
            mother_tongue_association_table).filter_by(lang_id=self.id).count()


spoken_association_table = Table(
    'spoken_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

written_association_table = Table(
    'written_lang_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

mother_tongue_association_table = Table(
    'mother_tongue_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)


certificate_association_table = Table(
    'certifcate_association',
    Base.metadata,
    Column(
        'translator_id',
        UUID,
        ForeignKey('translators.id'),
        nullable=False),
    Column('cert_id', UUID, ForeignKey('language_certificates.id'),
           nullable=False)
)

member_can_see = (
    'first_name',
    'last_name',
    'pers_id',
    'admission',
    'withholding_tax',
    'gender',
    'date_of_birth',
    'nationality',
    'address',
    'zip_code',
    'city',
    'drive_distance',
    'email',
    'tel_mobile',
    'tel_private',
    'tel_office',
    'availability',
    'mother_tongues',
    'languages_written',
    'languages_spoken'
)

editor_can_see = member_can_see + (
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner',
    'iban'
)


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
    def es_suggestion(self):
        return self.full_name

    @property
    def title(self):
        return self.full_name

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
    withholding_tax = Column(Text)

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
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
