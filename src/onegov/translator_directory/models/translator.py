from uuid import uuid4

from libres.db.models.timestamp import TimestampMixin
from sqlalchemy import Column, Text, Enum, Date, Integer, Table, ForeignKey, \
    Boolean
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.types import UUID
from onegov.translator_directory.models.documents import CertificateFile, \
    ApplicationFile

ADMISSIONS = ('uncertified', 'in_progress', 'certified')
GENDERS = ('F', 'M', 'N')


class Language(Base):

    __tablename__ = 'languages'

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)


spoken_association_table = Table(
    'spoken_lang_association',
    Base.metadata,
    Column(
        'translator_id', UUID, ForeignKey('translators.id'), nullable=False),
    Column('lang_id', UUID, ForeignKey('languages.id'), nullable=False)
)

written_association_table = Table(
    'written_lang_association',
    Base.metadata,
    Column(
        'translator_id', UUID, ForeignKey('translators.id'), nullable=False),
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


class Translator(Base, TimestampMixin):

    __tablename__ = 'translators'

    # id = Column(UUID, primary_key=True, default=uuid4)

    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)

    # Personal-Nr. used as primary key
    pers_id = Column(Integer, primary_key=True)

    # Zulassung / admission
    admission = Column(
        Enum(*ADMISSIONS, name='admission_state'),
        nullable=False,
        default='uncertified'
    )

    # Quellensteuer, Datatype?
    withholding_tax = Column(Text, nullable=False)

    gender = Column(Enum(*GENDERS, name='gender'), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    nationality = Column(Text, nullable=False)

    # Fields concerning address
    address = Column(Text, nullable=False)
    zip_code = Column(Text, nullable=False)
    city = Column(Text, nullable=False)

    # distance calculated from address to a fix point via api, im km
    drive_distance = Column(Integer)

    # AHV-Nr.
    social_sec_number = Column(Text, nullable=False)

    # Bank information
    bank_name = Column(Text, nullable=False)
    bank_address = Column(Text, nullable=False)
    account_owner = Column(Text, nullable=False)

    email = Column(Text, nullable=False, unique=True)

    # Which phone number should always be provided?
    tel_mobile = Column(Text, nullable=False)
    tel_private = Column(Text, nullable=True)
    tel_office = Column(Text, nullable=True)

    availability = Column(Text, nullable=True)

    # Translator can choose if he wants his name revealed...
    confirm_name_reveal = Column(Boolean, default=False, nullable=False)

    # The translator applies to be in the directory and gets a decision
    date_of_application = Column(Date, nullable=False)
    date_of_decision = Column(Date, nullable=False)

    # Language Information
    mother_tongue = Column(Text, ForeignKey('languages.name'), nullable=False)

    # Todo: sort these while queriing
    spoken_languages = relationship(
        "Language", secondary=spoken_association_table)
    written_languages = relationship(
        "Language", secondary=written_association_table)

    # Associated files
    certificates = associated(CertificateFile, 'files', 'one-to-many')
    applications = associated(ApplicationFile, 'files', 'one-to-many')

    # Bemerkungen
    comments = Column(Text, nullable=True)


