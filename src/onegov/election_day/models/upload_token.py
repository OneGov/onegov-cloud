from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID


class UploadToken(Base, TimestampMixin):
    """ Stores tokens for uploading using the REST interface. """

    __tablename__ = 'upload_tokens'

    #: Identifies the token
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The token
    token: Mapped[UUID] = mapped_column(
        unique=True,
        default=uuid4
    )
