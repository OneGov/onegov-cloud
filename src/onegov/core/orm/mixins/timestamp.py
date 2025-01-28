from __future__ import annotations

from onegov.core.orm.types import UTCDateTime
from sedate import utcnow
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy.schema import Column
from sqlalchemy.ext.hybrid import hybrid_property


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from sqlalchemy.sql.elements import ClauseElement


class TimestampMixin:
    """ Mixin providing created/modified timestamps for all records.

    The columns are deferred loaded as this is primarily for logging and future
    forensics.

    """

    @staticmethod
    def timestamp() -> datetime:
        return utcnow()

    def force_update(self) -> None:
        """ Forces the model to update by changing the modified parameter. """
        self.modified = self.timestamp()

    if TYPE_CHECKING:
        # FIXME: With SQLAlchemy 2.0 there is probably better support
        #        for type checking hybrid_properties/declared_attr, until
        #        then we have to pretend they are Columns in order for
        #        type checking to do the right thing, we still want
        #        to type check the implementation though, hence the
        #        `type:ignore[no-redef]` below, rather than putting
        #        the definitions inside the else block
        created: Column[datetime]
        modified: Column[datetime | None]
        last_change: Column[datetime]

    @declared_attr  # type:ignore[no-redef]
    def created(cls) -> Column[datetime]:
        # FIXME: This probably should have been nullable=False
        return Column(UTCDateTime, default=cls.timestamp)

    @declared_attr  # type:ignore[no-redef]
    def modified(cls) -> Column[datetime | None]:
        return Column(UTCDateTime, onupdate=cls.timestamp)

    @hybrid_property  # type:ignore[no-redef]
    def last_change(self) -> datetime:
        """ Returns the self.modified if not NULL, else self.created. """
        return self.modified or self.created

    @last_change.expression  # type:ignore[no-redef]
    def last_change(cls) -> ClauseElement:
        return func.coalesce(cls.modified, cls.created)
