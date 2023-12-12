from datetime import timedelta
from hashlib import sha256
from secrets import choice
from uuid import uuid4

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.orm.types import UTCDateTime
from sqlalchemy import func, Column, Index, Text
from sqlalchemy.ext.hybrid import hybrid_method


from typing import cast, Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement


ALPHABET = 'ABCDEFGHIJKLMNPQRSTUVWXYZ123456789'
DEFAULT_EXPIRES_AFTER = timedelta(hours=1)
DEFAULT_ACCESS_WINDOW = timedelta(days=1)


# NOTE: The same TAN can be generated multiple times, but this
#       should occur only rarely and since we only query the
#       TANs that haven't expired yet, it shouldn't cause any
#       issues.
def generate_tan() -> str:
    return ''.join(choice(ALPHABET) for _ in range(6))


class TAN(Base, TimestampMixin, ContentMixin):
    """
    A single use TAN for temporarily elevating access through e.g.
    a mobile phone number.

    """

    __tablename__ = 'tans'
    __table_args__ = (
        # TimestampMixin by default does not generate an index for
        # the created column, so we do it here instead
        Index('ix_tans_created', 'created'),
    )

    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    hashed_tan: 'Column[str]' = Column(
        Text,
        index=True,
        nullable=False
    )
    client: 'Column[str]' = Column(Text, nullable=False)
    expired: 'Column[datetime | None]' = Column(UTCDateTime, index=True)

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
    ) -> 'ColumnElement[bool]':

        now = cls.timestamp()
        expr = (cls.expired > now) | cls.expired.is_(None)

        if expires_after is not None:
            expr &= cls.created >= (now - expires_after)
        return expr

    def expire(self) -> None:
        if self.expired:
            raise ValueError('TAN already expired')

        self.expired = self.timestamp()


if TYPE_CHECKING:
    class _GeneratedTAN(TAN):
        tan: str


class TANCollection(GenericCollection[TAN]):

    def __init__(
        self,
        session: 'Session',
        expires_after: timedelta = DEFAULT_EXPIRES_AFTER
    ):
        super().__init__(session)
        self.expires_after = expires_after

    @property
    def model_class(self) -> type[TAN]:
        return TAN

    def query(self) -> 'Query[TAN]':
        return self.session.query(TAN).filter(
            TAN.is_active(self.expires_after)
        )

    def hash_tan(self, tan: str) -> str:
        return sha256(tan.encode('utf-8')).hexdigest()

    def add(  # type:ignore[override]
        self,
        *,
        client: str,
        **meta: Any
    ) -> '_GeneratedTAN':

        tan = generate_tan()
        obj = cast('_GeneratedTAN', TAN(
            hashed_tan=self.hash_tan(tan),
            client=client,
            meta=meta
        ))
        obj.tan = tan

        self.session.add(obj)
        self.session.flush()

        return obj

    def by_client(self, client: str) -> 'Query[TAN]':
        return self.query().filter(TAN.client == client)

    def by_tan(self, tan: str) -> TAN | None:
        hashed_tan = self.hash_tan(tan)
        return self.query().filter(TAN.hashed_tan == hashed_tan).first()


class TANAccess(Base, TimestampMixin):
    """
    This exists to keep track of which protected URLs have been accesed
    by any given TAN session.

    This allows us to throttle requests to protected resources.
    """

    __tablename__ = 'tan_accesses'
    __table_args__ = (
        # TimestampMixin by default does not generate an index for
        # the created column, so we do it here instead
        Index('ix_tan_accesses_created', 'created'),
    )

    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type: ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    # for an mTAN session this would be the phone number
    session_id: 'Column[str]' = Column(
        Text,
        index=True,
        nullable=False
    )

    # The url that was accessed
    url: 'Column[str]' = Column(
        Text,
        index=True,
        nullable=False
    )


class TANAccessCollection(GenericCollection[TANAccess]):

    def __init__(
        self,
        session: 'Session',
        session_id: str,
        access_window: timedelta = DEFAULT_ACCESS_WINDOW,
    ):
        super().__init__(session)
        self.session_id = session_id
        self.access_window = access_window

    @property
    def model_class(self) -> type[TANAccess]:
        return TANAccess

    def query(self) -> 'Query[TANAccess]':
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
