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
        ],
        default=['email', 'sms', 'webhooks']
    )

    def on_request(self):
        """ Adjusts the form to the given principal. """

        principal = self.request.app.principal

        self.notifications.choices = []
        if principal.email_notification:
            self.notifications.choices.append(('email', _("Email")))
        if principal.sms_notification:
            self.notifications.choices.append(('sms', _("SMS")))
        if principal.webhooks:
            self.notifications.choices.append(('webhooks', _("Webhooks")))
