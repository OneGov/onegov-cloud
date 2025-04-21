from __future__ import annotations

import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSONB
from onegov.core.orm.types import UUID
from onegov.user import User


class ImportLog(Base, TimestampMixin):
    """ Logs the summary of a KUB data import attempt. """

    __tablename__ = 'pas_import_logs'

    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid.uuid4
    )

    # user_id can be null if import is triggered by system/cron
    user_id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        ForeignKey('users.id'),
        nullable=False
    )
    user: relationship[User | None] = relationship('User')

    # Store summary counts or potentially full details JSON
    details: Column[dict[str, Any]] = Column(JSONB, nullable=False)

    # 'completed' or 'failed'
    status: Column[str] = Column(Text, nullable=False)

    # Optional: Add source identifiers like filenames if needed
    # source_info: Column[str | None] = Column(Text, nullable=True)
