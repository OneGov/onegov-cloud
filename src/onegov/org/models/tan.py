from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import func, Column, Index, Text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import Query, Session


DEFAULT_ACCESS_WINDOW = timedelta(days=1)


class TANAccess(Base, TimestampMixin):
    """
    This exists to keep track of which protected URLs have been accessed
    by any given TAN session.

    This allows us to throttle requests to protected resources.
    """

    __tablename__ = 'tan_accesses'
    __table_args__ = (
        # TimestampMixin by default does not generate an index for
        # the created column, so we do it here instead
        Index('ix_tan_accesses_created', 'created'),
    )

    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # for an mTAN session this would be the phone number
    session_id: Column[str] = Column(
        Text,
        index=True,
        nullable=False
    )

    # The url that was accessed
    url: Column[str] = Column(
        Text,
        index=True,
        nullable=False
    )


class TANAccessCollection(GenericCollection[TANAccess]):

    def __init__(
        self,
        session: Session,
        session_id: str,
        access_window: timedelta = DEFAULT_ACCESS_WINDOW,
    ):
        super().__init__(session)
        self.session_id = session_id
        self.access_window = access_window

    @property
    def model_class(self) -> type[TANAccess]:
        return TANAccess

    def query(self) -> Query[TANAccess]:
        cutoff = TANAccess.timestamp() - self.access_window
        return self.session.query(TANAccess).filter(
            TANAccess.session_id == self.session_id
        ).filter(TANAccess.created > cutoff)

    def add(self, *, url: str) -> TANAccess:  # type:ignore[override]
        access = self.by_url(url)
        if access is not None:
            # during the access_window subsequent accesses to the same
            # url are treated like a single access
            return access

        access = TANAccess(session_id=self.session_id, url=url)

        self.session.add(access)
        self.session.flush()

        return access

    def by_url(self, url: str) -> TANAccess | None:
        return self.query().filter(TANAccess.url == url).first()

    def count(self) -> int:
        return self.query().with_entities(func.count(TANAccess.id)).scalar()
