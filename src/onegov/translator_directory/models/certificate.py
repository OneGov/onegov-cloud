from uuid import uuid4

from sqlalchemy import Column, Text, Table, ForeignKey

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID


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


class LanguageCertificate(Base, TimestampMixin):

    __tablename__ = 'language_certificates'

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
