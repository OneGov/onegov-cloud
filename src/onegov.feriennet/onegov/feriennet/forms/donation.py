from onegov.feriennet import _
from onegov.form import Form
from onegov.feriennet.const import DEFAULT_DONATION_AMOUNTS
from onegov.feriennet.utils import format_donation_amounts
from wtforms.fields import SelectField
from wtforms.validators import InputRequired


class DonationForm(Form):

    amount = SelectField(
        label=_("My donation"),
        choices=(),
        validators=[InputRequired()]
    )

    def on_request(self):
        amounts = self.request.app.org.meta.get(
            'donation_amounts', DEFAULT_DONATION_AMOUNTS)

        readable = format_donation_amounts(amounts).split('\n')
        parsable = (f'{a:.2f}' for a in amounts)

        self.amount.choices = tuple(zip(parsable, readable))

    def ensure_valid_donation(self):
        # let's prevent shenanigans, like negative donations

        try:
            amount = float(self.amount.data)
        except ValueError:
            self.amount.errors = [_("Invalid amount")]
            return False

        if not (0 < amount < float('inf')):
            self.amount.errors = [_("Invalid amount")]
            return False
