from uuid import uuid4

from sqlalchemy import Column, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, backref

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID

NOTIFICATION_TYPES = ('info', 'reservation', 'reminder', 'cancellation')


class FsiNotificationTemplate(Base, ContentMixin, TimestampMixin):

    """
    For course event reservations, there are different types of emails.
    Each of the types have an sent property on the reservation table.

    """

    __tablename__ = 'fsi_notification_templates'

    __table_args__ = (UniqueConstraint('subject', 'owner_id',
                                       name='_subject_owner_id_uc'),)

    # the notification type used to choose the correct chameleon template
    type = Column(
        Enum(*NOTIFICATION_TYPES, name='notification_types'),
        default='info',
        nullable=False,
    )

    # the creator/owner of the record
    owner_id = Column(
        UUID, ForeignKey('fsi_attendees.id'), nullable=False)

    course_event_id = Column(
        UUID, ForeignKey('fsi_course_events.id'), nullable=False)

    course = relationship(
        'CourseEvent',
        backref=backref('template', uselist=False),
    )

    #: The public id of the notification template
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The subject of the notification would be according to template type
    subject = Column(Text, nullable=False)

    #: The body text injected into the template appearing on GUI
    text = Column(Text, nullable=False)

    def duplicate(self):
        return self.__class__(
            type=self.type,
            owner_id=self.owner_id,
            id=uuid4(),
            subject=self.subject,
            text=self.text
        )
