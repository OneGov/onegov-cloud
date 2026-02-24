from __future__ import annotations

from datetime import datetime
from sedate import utcnow
from sqlalchemy import case, func, and_, not_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement


class UTCPublicationMixin:

    #: Optional publication dates
    publication_start: Mapped[datetime | None]
    publication_end: Mapped[datetime | None]

    @hybrid_property
    def publication_started(self) -> bool:
        if not self.publication_start:
            return True
        return self.publication_start <= utcnow()

    @publication_started.inplace.expression
    @classmethod
    def _publication_started_expression(cls) -> ColumnElement[bool]:
        return case(
            (cls.publication_start == None, True),
            else_=cls.publication_start <= func.now()
        )

    @hybrid_property
    def publication_ended(self) -> bool:
        if not self.publication_end:
            return False
        return self.publication_end < utcnow()

    @publication_ended.inplace.expression
    @classmethod
    def _publication_ended_expression(cls) -> ColumnElement[bool]:
        return case(
            (cls.publication_end == None, False),
            else_=cls.publication_end < func.now()
        )

    @hybrid_property
    def published(self) -> bool:
        return self.publication_started and not self.publication_ended

    @published.inplace.expression
    @classmethod
    def _published_expression(cls) -> ColumnElement[bool]:
        return and_(cls.publication_started, not_(cls.publication_ended))
