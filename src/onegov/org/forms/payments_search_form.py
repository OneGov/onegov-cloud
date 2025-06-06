from __future__ import annotations

from wtforms import DateField
from onegov.form.core import Form
from onegov.form.fields import SelectField
from onegov.org import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay import PaymentCollection


class PaymentSearchForm(Form):

    start_date = DateField(
        label=_('From date'),
        fieldset=_('Filter Payments'),
    )

    end_date = DateField(
        label=_('To date'),
        fieldset=_('Filter Payments'),
    )

    ticket_start_date = DateField(
        label=_('Ticket created from date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
    )

    ticket_end_date = DateField(
        label=_('Ticket created to date'),
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
    )

    status = SelectField(
        label=_('Status'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('open', _('Open')),
            ('paid', _('Paid')),
            ('invoiced', _('Invoiced'))
        ],
        default='',
    )

    def apply_model(self, model: PaymentCollection) -> None:
        """Populate the form fields from the model's filter values."""
        self.start_date.data = model.start
        self.end_date.data = model.end
        self.status.data = model.status or ''
        self.ticket_start_date.data = model.ticket_start
        self.ticket_end_date.data = model.ticket_end
        self.payment_type.data = model.payment_type or ''

    def update_model(self, model: PaymentCollection) -> None:
        """Update the model's filter values from the form's data."""
        model.start = self.start_date.data
        model.end = self.end_date.data
        model.status = self.status.data or None
        model.ticket_start = self.ticket_start_date.data
        model.ticket_end = self.ticket_end_date.data
        model.payment_type = self.payment_type.data or None
        # Reset to the first page when filters change
        model.page = 0

    payment_type = SelectField(
        label=_('Payment Type'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('manual', _('Manual')),
            ('provider', _('Payment Provider'))
        ],
        default='',
    )
