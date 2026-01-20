from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import Column, Index, Text
from sqlalchemy.ext.hybrid import hybrid_method


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from sqlalchemy.sql import ColumnElement


DEFAULT_EXPIRES_AFTER = timedelta(hours=1)


class TAN(Base, TimestampMixin, ContentMixin):
    """
    A single use TAN for temporarily elevating access or to serve
    as a second authentication factor through e.g. a mobile phone
    number.

    """

    __tablename__ = 'tans'
    __table_args__ = (
        # TimestampMixin by default does not generate an index for
        # the created column, so we do it here instead
        Index('ix_tans_created', 'created'),
    )

    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    hashed_tan: Column[str] = Column(
        Text,
        index=True,
        nullable=False
    )
    scope: Column[str] = Column(Text, index=True, nullable=False)
    client: Column[str] = Column(Text, nullable=False)
    expired: Column[datetime | None] = Column(UTCDateTime, index=True)

    @hybrid_method
    def is_active(
        self,
        expires_after: timedelta | None = DEFAULT_EXPIRES_AFTER
    ) -> bool:

        now = self.timestamp()
        if self.expired and self.expired <= now:
            return False

        if expires_after is not None:
            if now >= (self.created + expires_after):
                return False
        return True

    @is_active.expression  # type:ignore[no-redef]
    def is_active(
        cls,
        expires_after: timedelta | None = DEFAULT_EXPIRES_AFTER
    ) -> ColumnElement[bool]:

        now = cls.timestamp()
        expr = (cls.expired > now) | cls.expired.is_(None)

        if expires_after is not None:
            expr &= cls.created >= (now - expires_after)
        return expr

    def expire(self) -> None:
        if self.expired:
            raise ValueError('TAN already expired')

        self.expired = self.timestamp()
