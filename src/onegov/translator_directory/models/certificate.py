from uuid import uuid4

from sqlalchemy import Column, Text

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID


class LanguageCertificate(Base, TimestampMixin):

    __tablename__ = 'language_certificates'

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(Text, nullable=False)
