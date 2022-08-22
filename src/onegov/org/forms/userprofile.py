from onegov.form import Form
from onegov.org import _
from wtforms.fields import RadioField
from wtforms.validators import InputRequired


class UserProfileForm(Form):
    """ Defines the settings form for user profiles. """

    ticket_statistics = RadioField(
        label=_("Send a periodic status e-mail."),
        fieldset=_("General"),
        default='weekly',
        validators=[InputRequired()],
        choices=(
            ('daily', _(
                "Daily (exluding the weekend)")),
            ('weekly', _(
                "Weekly (on mondays)")),
            ('monthly', _(
                "Monthly (on first monday of the month)")),
            ('never', _(
                "Never")),
        )
    )

    @property
    def enable_ticket_statistics(self):
        if not self.request.app.send_ticket_statistics:
            # no point in showing it if we don't send it.
            return False

        roles = self.request.app.settings.org.status_mail_roles
        return self.request.current_role in roles

    def on_request(self):
        if not self.enable_ticket_statistics:
            self.delete_field('ticket_statistics')

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'ticket_statistics',
        })

        if self.enable_ticket_statistics:
            model.data = model.data or {}
            model.data['ticket_statistics'] = self.ticket_statistics.data

    def process_obj(self, obj):
        super().process_obj(obj)

        if self.enable_ticket_statistics:
            self.ticket_statistics.data = (
                obj.data or {}).get('ticket_statistics', 'weekly')
