from onegov.form import Form
from onegov.org import _
from wtforms import BooleanField


class UserProfileForm(Form):
    """ Defines the settings form for user profiles. """

    daily_ticket_statistics = BooleanField(_("Send a daily status e-mail."))

    @property
    def enable_daily_ticket_statistics(self):
        roles = self.request.app.settings.org.status_mail_roles
        return self.request.current_role in roles

    def on_request(self):
        if not self.enable_daily_ticket_statistics:
            self.delete_field('daily_ticket_statistics')

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'daily_ticket_statistics'
        })

        if self.enable_daily_ticket_statistics:
            model.data = model.data or {}
            model.data['daily_ticket_statistics']\
                = self.daily_ticket_statistics.data

    def process_obj(self, obj):
        super().process_obj(obj)

        if self.enable_daily_ticket_statistics:
            self.daily_ticket_statistics.data\
                = (obj.data or {}).get('daily_ticket_statistics', True)
