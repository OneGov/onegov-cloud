from onegov.form import Form
from onegov.town import _
from wtforms import BooleanField


class UserProfileForm(Form):
    """ Defines the settings form for onegov town. """

    daily_ticket_statistics = BooleanField(_(
        "Send me a daily e-mail with information about the website's state."
    ))

    def update_model(self, model):
        if model.data is None:
            model.data = {}

        model.data['daily_ticket_statistics']\
            = self.data['daily_ticket_statistics']

    def apply_model(self, model):
        self.daily_ticket_statistics.data\
            = (model.data or {}).get('daily_ticket_statistics', True)
