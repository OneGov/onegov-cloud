from __future__ import annotations

from sedate import utcnow
from sqlalchemy import Column, case, func, and_, not_
from sqlalchemy.ext.hybrid import hybrid_property
from onegov.core.orm.types import UTCDateTime


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ClauseElement


class UTCPublicationMixin:

    #: Optional publication dates
    publication_start = Column(UTCDateTime, nullable=True)
    publication_end = Column(UTCDateTime, nullable=True)

    if TYPE_CHECKING:
        # FIXME: With SQLAlchemy 2.0 there is probably better support
        #        for type checking hybrid_properties, until then we
        #        have to pretend they are Columns in order for
        #        type checking to do the right thing, we still want
        #        to type check the implementation though, hence the
        #        `type:ignore[no-redef]` below, rather than putting
        #        the definitions inside the else block
        publication_started: Column[bool]
        publication_ended: Column[bool]
        published: Column[bool]

    @hybrid_property  # type:ignore[no-redef]
    def publication_started(self) -> bool:
        if not self.publication_start:
            return True
        return self.publication_start <= utcnow()

    @publication_started.expression  # type:ignore[no-redef]
    def publication_started(cls) -> ClauseElement:
        return case(
            (cls.publication_start == None, True),
            else_=cls.publication_start <= func.now()
        )

    @hybrid_property  # type:ignore[no-redef]
    def publication_ended(self) -> bool:
        if not self.publication_end:
            return False
        return self.publication_end < utcnow()

    @publication_ended.expression  # type:ignore[no-redef]
    def publication_ended(cls) -> ClauseElement:
        return case(
            (cls.publication_end == None, False),
            else_=cls.publication_end < func.now()
        )

    @hybrid_property  # type:ignore[no-redef]
    def published(self) -> bool:
        return self.publication_started and not self.publication_ended

    @published.expression  # type:ignore[no-redef]
    def published(cls) -> ClauseElement:
        return and_(cls.publication_started, not_(cls.publication_ended))
