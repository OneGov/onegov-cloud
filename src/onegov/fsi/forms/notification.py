from wtforms import StringField, TextAreaField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.fsi import _
from cached_property import cached_property


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

    def apply_model(self, model):
        self.subject.data = model.subject
        self.text.data = model.text

    def update_model(self, model):
        model.subject = self.subject.data
        model.text = self.text.data


class NotificationTemplateSendForm(Form):

    recipients = MultiCheckboxField(
        label=_("Recipients"),
    )

    @property
    def has_recipients(self):
        return len(self.attendees) > 0

    @cached_property
    def attendees(self):
        return [a for a in self.model.course_event.attendees if a.active]

    @property
    def recipients_choices(self):
        return [(a.id, a.email) for a in self.attendees]

    def on_request(self):
        choices = self.recipients_choices
        self.recipients.choices = choices
        self.recipients.data = [c[0] for c in choices]
