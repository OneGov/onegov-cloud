from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid


class UploadToken(Base, TimestampMixin):
    """ Stores tokens for uploading using the REST interface. """

    __tablename__ = 'upload_tokens'

    #: Identifies the token
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The token
    token: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        unique=True,
        default=uuid4,
        nullable=False
    )
