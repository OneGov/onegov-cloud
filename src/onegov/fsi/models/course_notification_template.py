from __future__ import annotations

from datetime import datetime
from markupsafe import Markup
from sqlalchemy import ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.fsi import _


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.fsi.request import FsiRequest
    from typing import Self, TypeAlias
    from .course_event import CourseEvent


NotificationType: TypeAlias = Literal[
    'info', 'reservation', 'reminder', 'cancellation',
]

NOTIFICATION_TYPES: tuple[NotificationType, ...] = (
    'info', 'reservation', 'reminder', 'cancellation')
NOTIFICATION_TYPE_TRANSLATIONS = (
    _('Info Mail'), _('Subscription Confirmation'),
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
def template_type_choices(
    request: FsiRequest | None = None
) -> tuple[tuple[str, str], ...]:

    if request:
        translations: Iterable[str] = (
            request.translate(t) for t in NOTIFICATION_TYPE_TRANSLATIONS)
    else:
        translations = NOTIFICATION_TYPE_TRANSLATIONS
    return tuple(
        (val, key) for val, key in zip(NOTIFICATION_TYPES,
                                       translations))


def get_template_default(
    # FIXME: We can improve the type of context in SQLAlchemy 2.0
    context: Any,
    type: str | None = None
) -> str:
    t = type or context.current_parameters.get('type')
    return GERMAN_TYPE_TRANSLATIONS[t]


def template_name(
    type: NotificationType | Literal['invitation'],
    request: FsiRequest | None = None
) -> str:
    try:
        if type == 'invitation':
            text = _('Course Subscription Invitation')
        else:
            # FIXME: Why not just collapse these into a dictionary?
            text = NOTIFICATION_TYPE_TRANSLATIONS[
                NOTIFICATION_TYPES.index(type)
            ]
    except ValueError as exception:
        raise AssertionError(
            'There are 5 notifications types allowed'
        ) from exception
    return request.translate(text) if request else text


class CourseInvitationTemplate:

    """
    This is kind of a dummy db model for using as the template for
    CourseInviteMailLayout. If needed, this can be replaced with
    a real model without changing too much code.
    """

    text = None
    text_html = None
    type: Literal['invitation'] = 'invitation'
    subject = get_template_default(None, type)


class CourseNotificationTemplate(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'fsi_notification_templates'

    __table_args__ = (UniqueConstraint('course_event_id', 'type', 'subject',
                                       name='_course_type_subject_uc'),
                      )

    # the notification type used to choose the correct chameleon template
    type: Mapped[NotificationType] = mapped_column(
        Enum(*NOTIFICATION_TYPES, name='notification_types'),
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'fsi_notification_templates'
    }

    # One-To-Many relationship with course
    course_event_id: Mapped[UUID] = mapped_column(
        ForeignKey('fsi_course_events.id')
    )

    course_event: Mapped[CourseEvent] = relationship(
        back_populates='notification_templates',
        overlaps='info_template,reservation_template,'
                 'cancellation_template,reminder_template'
    )

    #: The public id of the notification template
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The subject of the notification would be according to template type
    subject: Mapped[str | None] = mapped_column(default=get_template_default)

    #: The body text injected in plaintext (not html)
    text: Mapped[str | None]

    # when email based on template was sent last time
    last_sent: Mapped[datetime | None]

    def duplicate(self) -> Self:
        return self.__class__(
            type=self.type,
            id=uuid4(),
            subject=self.subject,
            text=self.text
        )

    @property
    def text_html(self) -> Markup | None:
        if not self.text:
            return None

        return Markup(' ').join(
            Markup('<p>{}</p>').format(part)
            for part in self.text.split('\n') if part
        )


class InfoTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'info'}


class SubscriptionTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reservation'}


class ReminderTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'reminder'}


class CancellationTemplate(CourseNotificationTemplate):
    __mapper_args__ = {'polymorphic_identity': 'cancellation'}
