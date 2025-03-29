from __future__ import annotations

from onegov.core.orm.types import UTCDateTime
from uuid import uuid4
from onegov.core.collection import GenericCollection
from sedate import utcnow
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from onegov.core.orm.types import JSON, UUID
from onegov.core.orm import Base


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from sqlalchemy.orm import Query, Session
    from onegov.org.models import News


class PushNotification(Base):
    """
    Keeps track of all outbound push notifications to prevent duplicates.
    """
    __tablename__: ClassVar[str] = 'push_notification'

    #: The internal ID of the notification
    id: Column[uuid.UUID] = Column(
        UUID,  # type: ignore[arg-type]
        nullable=False,
        primary_key=True,
        default=uuid4
    )

    #: The ID of the news item that triggered the notification
    news_id: Column[int] = Column(
        Integer,
        ForeignKey('pages.id', ondelete='CASCADE'),
        nullable=False
    )
    news: relationship[News] = relationship(
        'News',
        backref=backref('sent_notifications', passive_deletes=True),
        foreign_keys=[news_id]
    )

    #: The topic/channel the notification was sent to
    topic_id: Column[str] = Column(String, nullable=False)

    #: When the notification was sent
    sent_at = Column(UTCDateTime, nullable=False, default=utcnow)

    #: Response information from the notification service
    response_data: Column[dict[str, Any] | None] = Column(JSON, nullable=True)

    @classmethod
    def was_notification_sent(
        cls, session: Session, news_id: int, topic_id: str
    ) -> bool:
        return (
            session.query(cls)
            .filter(cls.news_id == news_id, cls.topic_id == topic_id)
            .first()
            is not None
        )

    @classmethod
    def record_sent_notification(
        cls,
        session: Session,
        news_id: int,
        topic_id: str,
        response_data: dict[str, Any] | None
    ) -> PushNotification:
        notification = cls(
            news_id=news_id,
            topic_id=topic_id,
            sent_at=utcnow(),
            response_data=response_data
        )
        session.add(notification)
        session.flush()
        return notification

    # For each topic_id inside a news, there should be only one notification
    __table_args__ = (
        UniqueConstraint('news_id', 'topic_id', name='uix_news_topic'),
    )


class PushNotificationCollection(GenericCollection[PushNotification]):
    """Simple collection for sent notifications."""

    @property
    def model_class(self) -> type[PushNotification]:
        return PushNotification

    def query(self) -> Query[PushNotification]:
        return super().query().order_by(PushNotification.sent_at.desc())
