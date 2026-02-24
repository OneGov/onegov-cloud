from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.pas import _
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


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

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    # user_id can be null if import is triggered by system/cron
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey('users.id'))
    user: Mapped[User | None] = relationship()

    # Store summary counts or potentially full details JSON
    details: Mapped[dict[str, Any]]

    # 'completed' or 'failed'
    status: Mapped[str]

    # 'cli', 'upload', or 'automatic'
    import_type: Mapped[str]

    # This is the json response from the api, we store it to be able to
    # reconstruct how certain imports were run. This will be useful to
    # debug issues. But we don't want to store it every time, as these are
    # several MBs of text and the sync cronjob runs regularly.
    # These are deferred by default to avoid loading large JSON data
    people_source: Mapped[Any | None] = mapped_column(
        JSONB,
        deferred=True
    )
    organizations_source: Mapped[Any | None] = mapped_column(
        JSONB,
        deferred=True
    )
    memberships_source: Mapped[Any | None] = mapped_column(
        JSONB,
        deferred=True
    )
