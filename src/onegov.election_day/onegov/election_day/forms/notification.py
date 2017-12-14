from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.validators import InputRequired


class TriggerNotificationForm(Form):

    notifications = MultiCheckboxField(
        label=_("Notifications"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        """ Adjusts the form to the given principal. """

        principal = self.request.app.principal

        self.notifications.choices = []
        self.notifications.data = []
        if principal.email_notification:
            self.notifications.choices.append(('email', _("Email")))
            self.notifications.data.append('email')
        if principal.sms_notification:
            self.notifications.choices.append(('sms', _("SMS")))
            self.notifications.data.append('sms')
        if principal.webhooks:
            self.notifications.choices.append(('webhooks', _("Webhooks")))
            self.notifications.data.append('webhooks')
