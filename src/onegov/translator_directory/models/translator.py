from uuid import uuid4
from onegov.translator_directory import _
from libres.db.models.timestamp import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Table, ForeignKey, \
    Boolean
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import UUID
from onegov.translator_directory.models.documents import CertificateFile, \
    ApplicationFile, ClarificationFile, ConfirmationFile, ComplaintFile, \
    CorrespondenceFile, MiscFile

ADMISSIONS = ('uncertified', 'in_progress', 'certified')
GENDERS = ('M', 'F', 'N')
GENDERS_DESC = (_('masculin'), _('feminin'), 'neutral')
CERTIFICATES = ('ZHAW', 'OGZH')


class Language(Base):

    __tablename__ = 'languages'

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)


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
    'mother_tongue',
    'languages_written',
    'languages_spoken'
)

editor_can_see = member_can_see + (
    'social_sec_number',
    'bank_name',
    'bank_address',
    'account_owner'
)


class TranslatorDocumentsMixin(object):
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


class Translator(Base, TimestampMixin, TranslatorDocumentsMixin):

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
    drive_distance = Column(Integer)

    # AHV-Nr.
    social_sec_number = Column(Text)

    # Bank information
    bank_name = Column(Text)
    bank_address = Column(Text)
    account_owner = Column(Text)

    email = Column(Text)

    # Which phone number should always be provided?
    tel_mobile = Column(Text,)
    tel_private = Column(Text)
    tel_office = Column(Text)

    availability = Column(Text)

    # Not set is also a state, namely not known here
    confirm_name_reveal = Column(Boolean)

    # The translator applies to be in the directory and gets a decision
    date_of_application = Column(Date)
    date_of_decision = Column(Date)

    # Language Information
    mother_tongue_id = Column(
        UUID, ForeignKey('languages.id')
    )
    mother_tongue = relationship('Language')

    # Todo: sort these while queriing
    spoken_languages = relationship(
        "Language", secondary=spoken_association_table, backref="speakers"
    )
    written_languages = relationship(
        "Language", secondary=written_association_table, backref='writers')

    # Nachweis der Voraussetzungen
    proof_of_preconditions = Column(Text)

    # Referenzen Behörden (???)
    agency_references = Column(Text)

    # Ausbildung Dolmetscher
    education_as_interpreter = Column(Boolean, default=False, nullable=False)

    # pre-defined certificates
    certificate = Column(Enum(*CERTIFICATES, name='certificate'))

    # Bemerkungen
    comments = Column(Text)

    # field for hiding to users except admins
    hidden = Column(Boolean, default=False, nullable=False)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
