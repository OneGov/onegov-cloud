from __future__ import annotations

from functools import cached_property
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.fsi import _
from wtforms.fields import StringField, TextAreaField
from wtforms.validators import InputRequired
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseAttendee, CourseNotificationTemplate
    from wtforms.fields.choices import _Choice


class NotificationForm(Form):

    subject = StringField(
        label=_('Email Subject'),
        render_kw={'size': 6, 'clear': True},
        validators=[
            InputRequired()
        ],
    )

    text = TextAreaField(
        label=_('Email Text'),
        render_kw={'rows': 10, 'cols': 12},
    )

    def apply_model(self, model: CourseNotificationTemplate) -> None:
        self.subject.data = model.subject
        self.text.data = model.text

    def update_model(self, model: CourseNotificationTemplate) -> None:
        model.subject = self.subject.data
        model.text = self.text.data


class NotificationTemplateSendForm(Form):

    model: CourseNotificationTemplate

    recipients = MultiCheckboxField(
        label=_('Recipients'),
        coerce=lambda x: x if isinstance(x, UUID) else UUID(x)
    )

    @property
    def has_recipients(self) -> bool:
        return len(self.attendees) > 0

    @cached_property
    def attendees(self) -> list[CourseAttendee]:
        return [a for a in self.model.course_event.attendees if a.active]

    @cached_property
    def recipients_choices(self) -> list[_Choice]:
        return [(a.id, a.email) for a in self.attendees]

    def on_request(self) -> None:
        choices = self.recipients_choices
        self.recipients.choices = choices
        self.recipients.data = [c[0] for c in choices]
