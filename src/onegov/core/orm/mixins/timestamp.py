from __future__ import annotations

from datetime import datetime
from sedate import utcnow
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement


class TimestampMixin:
    """ Mixin providing created/modified timestamps for all records.

    The columns are deferred loaded as this is primarily for logging and future
    forensics.

    """

    @staticmethod
    def timestamp() -> datetime:
        return utcnow()

    created: Mapped[datetime] = mapped_column(default=timestamp)
    modified: Mapped[datetime | None] = mapped_column(onupdate=timestamp)

    def force_update(self) -> None:
        """ Forces the model to update by changing the modified parameter. """
        self.modified = self.timestamp()

    @hybrid_property
    def last_change(self) -> datetime:
        """ Returns the self.modified if not NULL, else self.created. """
        return self.modified or self.created

    @last_change.inplace.expression
    @classmethod
    def _last_change_expression(cls) -> ColumnElement[datetime]:
        return func.coalesce(cls.modified, cls.created)
