from uuid import uuid4

from sqlalchemy import Column, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from onegov.fsi import _

NOTIFICATION_TYPES = ('info', 'reservation', 'reminder', 'cancellation')
NOTIFICATION_TYPE_TRANSLATIONS = (
    _('Info Mail'), _('Reservation Confirmation'),
    _('Event Reminder'), _('Cancellation Confirmation')
)


# for forms...
def template_type_choices():
    return tuple(
        (val, key) for val, key in zip(NOTIFICATION_TYPES,
                                       NOTIFICATION_TYPE_TRANSLATIONS))


class FsiNotificationTemplate(Base, ContentMixin, TimestampMixin):

    """
    For course event reservations, there are different types of emails.
    Each of the types have an sent property on the reservation table.

    """

    __tablename__ = 'fsi_notification_templates'

    __table_args__ = (UniqueConstraint('course_event_id', 'type', 'subject',
                                       name='_course_type_subject_uc'),
                      )

    # the notification type used to choose the correct chameleon template
    type = Column(
        Enum(*NOTIFICATION_TYPES, name='notification_types'),
        nullable=False,
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'fsi_notification_templates'
    }

    # the creator/owner of the record
    owner_id = Column(
        UUID, ForeignKey('fsi_attendees.id'), nullable=True)

    # One-To-Many relationship with course
    course_event_id = Column(
        UUID, ForeignKey('fsi_course_events.id'), nullable=False)

    course_event = relationship('CourseEvent',
                                back_populates='notification_templates')

    #: The public id of the notification template
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The subject of the notification would be according to template type
    subject = Column(Text, nullable=False, default='Example Subject')

    #: The body text injected into the template appearing on GUI
    text = Column(Text, nullable=False, default='Example Text')

    def duplicate(self):
        return self.__class__(
            type=self.type,
            owner_id=self.owner_id,
            id=uuid4(),
            subject=self.subject,
            text=self.text
        )


class InfoTemplate(FsiNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'info'}


class ReservationTemplate(FsiNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reservation'}


class ReminderTemplate(FsiNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reminder'}


class CancellationTemplate(FsiNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'cancellation'}
