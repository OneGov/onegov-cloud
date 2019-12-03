from wtforms import StringField, TextAreaField

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.fsi import _
from onegov.fsi.utils import handle_empty_p_tags


class NotificationForm(Form):

    subject = StringField(
        label=_('Email Subject'),
        render_kw={'size': 6, 'clear': True}
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
        model.text = handle_empty_p_tags(self.text.data)


class NotificationTemplateSendForm(Form):

    recipients = MultiCheckboxField(
        label=_("Recipients"),
    )

    @property
    def has_recipients(self):
        return bool(self.model.course_event.attendees.count())

    @property
    def recipients_emails(self):
        return [a.email for a in self.model.course_event.attendees]

    @property
    def recipients_choices(self):
        return [
            (f'{a.id}-{a.email}', a.email)
            for a in self.model.course_event.attendees
        ]

    def on_request(self):
        self.recipients.choices = self.recipients_choices
        self.recipients.data = self.recipients_emails
