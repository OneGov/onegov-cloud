from __future__ import annotations

import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.orm.types import JSON


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import User


class ImportLog(Base, TimestampMixin):
    """ Logs the summary of a KUB data import attempt. """

    __tablename__ = 'par_import_logs'

    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid.uuid4
    )

    # user_id can be null if import is triggered by system/cron
    user_id: Column[uuid.UUID | None] = Column(
        UUID,  # type: ignore[arg-type]
        ForeignKey('users.id'),
        nullable=True
    )
    user: relationship[User | None] = relationship('User')

    # Store summary counts or potentially full details JSON
    details: Column[dict[str, Any]] = Column(JSON, nullable=False)

    # 'completed' or 'failed'
    status: Column[str] = Column(Text, nullable=False)

    # Optional: Add source identifiers like filenames if needed
    # source_info: Column[str | None] = Column(Text, nullable=True)
