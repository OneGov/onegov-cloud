from __future__ import annotations

from datetime import datetime
from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from sedate import utcnow
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session
    from onegov.org.models import News


class PushNotification(Base):
    """
    Keeps track of all outbound push notifications to prevent duplicates.
    """
    __tablename__ = 'push_notification'

    #: The internal ID of the notification
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The ID of the news item that triggered the notification
    news_id: Mapped[int] = mapped_column(
        ForeignKey('pages.id', ondelete='CASCADE')
    )
    news: Mapped[News] = relationship(
        back_populates='sent_notifications',
        foreign_keys=[news_id]
    )

    #: The topic/channel the notification was sent to
    topic_id: Mapped[str] = mapped_column(String)

    #: When the notification was sent
    sent_at: Mapped[datetime] = mapped_column(default=utcnow)

    #: Response information from the notification service
    response_data: Mapped[dict[str, Any] | None]

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
