from uuid import uuid4

from sqlalchemy import Column, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.fsi import _

NOTIFICATION_TYPES = ('info', 'reservation', 'reminder', 'cancellation')
NOTIFICATION_TYPE_TRANSLATIONS = (
    _('Info Mail'), _('Reservation Confirmation'),
    _('Event Reminder'), _('Cancellation Confirmation')
)

GERMAN_TYPE_TRANSLATIONS = {
    'info': 'Info E-Mail Kursveranstaltung',
    'reservation': 'Anmeldungsbestätigung',
    'reminder': 'Erinnerung Kursdurchführung',
    'cancellation': 'Absage Kursveranstaltung',
    'invitation': 'Einladung für Kursanmeldung'
}


# for forms...
def template_type_choices(request=None):
    if request:
        translations = (
            request.translate(t) for t in NOTIFICATION_TYPE_TRANSLATIONS)
    else:
        translations = NOTIFICATION_TYPE_TRANSLATIONS
    return tuple(
        (val, key) for val, key in zip(NOTIFICATION_TYPES,
                                       translations))


def get_template_default(context, type=None):
    t = type or context.current_parameters.get('type')
    return GERMAN_TYPE_TRANSLATIONS[t]


def template_name(type, request=None):
    try:
        text = NOTIFICATION_TYPE_TRANSLATIONS[NOTIFICATION_TYPES.index(type)]
    except ValueError:
        if type == 'invitation':
            text = _('Course Subscription Invitation')
        else:
            raise AssertionError('There are 5 notifications types allowed')
    return request.translate(text) if request else text


class CourseInvitationTemplate:

    """
    This is cind of a dummy db model for using as the template for
    CourseInviteMailLayout. If needed, this can be replaced with
    a real model without changing too much code.
    """

    text = None
    text_html = None
    type = 'invitation'
    subject = get_template_default(None, type)


class CourseNotificationTemplate(Base, ContentMixin, TimestampMixin):

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

    # One-To-Many relationship with course
    course_event_id = Column(
        UUID, ForeignKey('fsi_course_events.id'), nullable=False)

    course_event = relationship('CourseEvent',
                                back_populates='notification_templates')

    #: The public id of the notification template
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The subject of the notification would be according to template type
    subject = Column(Text, default=get_template_default)

    #: The body text injected in plaintext (not html)
    text = Column(Text)

    # when email based on template was sent last time
    last_sent = Column(UTCDateTime)

    def duplicate(self):
        return self.__class__(
            type=self.type,
            id=uuid4(),
            subject=self.subject,
            text=self.text
        )

    @property
    def text_html(self):
        if not self.text:
            return None
        parts = self.text.replace('\n\n', '\n').split('\n')
        rendered = " ".join((f'<p>{el}</p>' for el in parts if el))
        return rendered


class InfoTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'info'}


class ReservationTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reservation'}


class ReminderTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reminder'}


class CancellationTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'cancellation'}
