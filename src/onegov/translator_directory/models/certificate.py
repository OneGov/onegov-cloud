from __future__ import annotations

from uuid import uuid4, UUID

from sqlalchemy import Column, ForeignKey, Table, UUID as UUIDType
from sqlalchemy.orm import mapped_column, relationship, Mapped

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.models.translator import Translator


certificate_association_table = Table(
    'certifcate_association',
    Base.metadata,
    Column(
        'translator_id',
        UUIDType(as_uuid=True),
        ForeignKey('translators.id'),
        nullable=False
    ),
    Column(
        'cert_id',
        UUIDType(as_uuid=True),
        ForeignKey('language_certificates.id'),
        nullable=False
    )
)


class LanguageCertificate(Base, TimestampMixin):

    __tablename__ = 'language_certificates'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str]

    owners: Mapped[list[Translator]] = relationship(
        secondary=certificate_association_table,
        back_populates='certificates'
    )
