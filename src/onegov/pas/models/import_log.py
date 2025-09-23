from __future__ import annotations

from sqlalchemy.dialects.postgresql.json import JSONB
import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship, deferred
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.orm.types import JSON
from onegov.pas import _


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import User


class ImportLog(Base, TimestampMixin):
    """ Logs the summary of a KUB data import attempt. """

    __tablename__ = 'pas_import_logs'

    # Status translations for .po file extraction
    _('completed')
    _('failed')
    _('pending')
    _('timeout')

    # Import type translations for .po file extraction
    _('cli')
    _('automatic')
    _('upload')

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

    # 'cli', 'upload', or 'automatic'
    import_type: Column[str] = Column(Text, nullable=False)

    # This is the json response from the api, we store it to be able to
    # reconstruct how certain imports were run. This will be useful to
    # debug issues. But we don't want to store it every time, as these are
    # several MBs of text and the sync cronjob runs regularly.
    # These are deferred by default to avoid loading large JSON data
    people_source: Column[Any] = deferred(Column(JSONB, nullable=True))
    organizations_source: Column[Any] = deferred(Column(
        JSONB, nullable=True
    ))
    memberships_source: Column[Any] = deferred(Column(JSONB, nullable=True))
