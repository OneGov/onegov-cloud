from uuid import uuid4

from sqlalchemy import Column, Text, ForeignKey, Enum

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime

NOTIFICATION_TYPES = ('info', 'reservation', 'cancelation')


class FsiNotificationTemplate(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'fsi_notification_templates'

    # the notification type used to choose the correct chameleon template
    type = Column(
        Enum(*NOTIFICATION_TYPES, name='notification_types'),
        default='info',
        nullable=False,
    )

    # the creator/owner of the record
    owner_id = Column(
        UUID, ForeignKey('fsi_attendees.id'), nullable=False)

    #: The public id of the notification template
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The subject of the notification would be according to template type
    # subject = Column(Text, nullable=False, unique=True)

    #: The body text injected into the template
    text = Column(Text, nullable=False)

    #: The date the notification was last sent
    last_sent = Column(UTCDateTime, nullable=True)
