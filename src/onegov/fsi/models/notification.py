from uuid import uuid4

from sqlalchemy import Column, Text, ForeignKey, Enum

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime


class FsiNotification(Base, TimestampMixin):

    """
    For course event reservations, there are different types of emails.
    Each of the types have an sent property on the reservation table.

    """

    __tablename__ = 'fsi_notifications'

    id = Column(UUID, primary_key=True, default=uuid4)

    # the linking reservation
    reservation_id = Column(
        UUID, ForeignKey('fsi_reservations.id'), nullable=False)

    # Fields for the NotificationTemplate.NOTIFICATION_TYPES
    invitation_sent = Column(UTCDateTime)
    reminder_sent = Column(UTCDateTime)
    cancellation_sent = Column(UTCDateTime)
    info_sent = Column(UTCDateTime)
