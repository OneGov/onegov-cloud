from onegov.form import Form
from onegov.org import _
from wtforms import BooleanField


class UserProfileForm(Form):
    """ Defines the settings form for user profiles. """

    daily_ticket_statistics = BooleanField(_("Send a daily status e-mail."))

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'daily_ticket_statistics'
        })

        model.data = model.data or {}
        model.data['daily_ticket_statistics']\
            = self.daily_ticket_statistics.data

    def process_obj(self, obj):
        super().process_obj(obj)

        self.daily_ticket_statistics.data\
            = (obj.data or {}).get('daily_ticket_statistics', True)
