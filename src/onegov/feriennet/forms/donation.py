from __future__ import annotations

from onegov.feriennet import _
from onegov.form import Form
from onegov.feriennet.const import DEFAULT_DONATION_AMOUNTS
from onegov.feriennet.utils import format_donation_amounts
from wtforms.fields import SelectField
from wtforms.validators import InputRequired, ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest


class DonationForm(Form):

    request: FeriennetRequest

    amount = SelectField(
        label=_('My donation'),
        choices=(),
        validators=[InputRequired()]
    )

    def on_request(self) -> None:
        amounts = self.request.app.org.meta.get(
            'donation_amounts', DEFAULT_DONATION_AMOUNTS
        ) or DEFAULT_DONATION_AMOUNTS

        readable = format_donation_amounts(amounts).split('\n')
        parsable = (f'{a:.2f}' for a in amounts)

        self.amount.choices = list(zip(parsable, readable))

    def validate_amount(self, field: SelectField) -> None:
        # let's prevent shenanigans, like negative donations

        try:
            amount = float(self.amount.data)
        except ValueError:
            raise ValidationError(_('Invalid amount')) from None

        if not (0 < amount < float('inf')):
            raise ValidationError(_('Invalid amount'))
