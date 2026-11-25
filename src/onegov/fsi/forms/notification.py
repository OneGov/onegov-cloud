from functools import cached_property
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.utils import coerce_uuid
from onegov.fsi import _
from wtforms.fields import SelectChoice, StringField, TextAreaField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseAttendee, CourseNotificationTemplate


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
        coerce=coerce_uuid
    )

    @property
    def has_recipients(self) -> bool:
        return len(self.attendees) > 0

    @cached_property
    def attendees(self) -> list[CourseAttendee]:
        return [a for a in self.model.course_event.attendees if a.active]

    @cached_property
    def recipients_choices(self) -> list[SelectChoice]:
        return [SelectChoice(a.id.hex, a.email) for a in self.attendees]

    def on_request(self) -> None:
        choices = self.recipients_choices
        self.recipients.choices = choices
        self.recipients.data = [coerce_uuid(c.value) for c in choices]
