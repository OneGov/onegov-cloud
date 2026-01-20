from __future__ import annotations

from decimal import Decimal
from onegov.form import Form
from onegov.form.validators import If
from onegov.org import _
from onegov.pay.constants import MAX_AMOUNT
from wtforms.fields import DecimalField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket import Ticket


class ManualInvoiceItemForm(Form):

    model: Ticket

    booking_text = StringField(
        label=_('Booking Text'),
        validators=(InputRequired(), )
    )

    cost_object = StringField(
        label=_('Cost center / cost unit')
    )

    kind = RadioField(
        label=_('Kind'),
        default='discount',
        choices=(
            ('discount', _('Discount')),
            ('surcharge', _('Surcharge'))
        )
    )

    discount = DecimalField(
        label=_('Discount'),
        places=2,
        validators=(InputRequired(), NumberRange(Decimal('0'), MAX_AMOUNT)),
        depends_on=('kind', 'discount')
    )

    surcharge = DecimalField(
        label=_('Surcharge'),
        places=2,
        validators=(InputRequired(), NumberRange(Decimal('0'), MAX_AMOUNT)),
        depends_on=('kind', 'surcharge')
    )

    @property
    def amount(self) -> Decimal:
        if self.kind.data == 'discount':
            assert self.discount.data is not None
            return -self.discount.data
        elif self.kind.data == 'surcharge':
            assert self.surcharge.data is not None
            return self.surcharge.data
        else:
            raise NotImplementedError

    def on_request(self) -> None:
        invoice = self.model.invoice
        # HACK: Getting at the validator and modifying it like this
        #       is not very robust. We should consider adding a
        #       `validate_discount` method instead.
        if_validator = self.discount.validators[0]
        assert isinstance(if_validator, If)
        validator = if_validator.validators[1]
        assert isinstance(validator, NumberRange)
        if invoice is None:
            # restore the default max just in case
            validator.max = MAX_AMOUNT
        else:
            # NOTE: Make sure we don't discount to a negative price
            #       it can still happen later on through modifying
            #       form inputs or reservations, but we shouldn't
            #       create negative amounts eagerly
            validator.max = invoice.outstanding_amount
