from __future__ import annotations

from onegov.form.core import Form
from onegov.form.fields import SelectField, TimezoneDateTimeField
from onegov.form.validators import StrictOptional
from onegov.org import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay import PaymentCollection


class PaymentSearchForm(Form):

    STATUS_CHOICES = [
        ('', _('All')),
        ('open', _('Open')),
        ('paid', _('Paid')),
        ('invoiced', _('Invoiced'))
    ]

    PAYMENT_TYPE_CHOICES = [
        ('', _('All')),
        ('manual', _('Manual')),
        ('provider', _('Payment Provider'))
    ]

    tz = 'Europe/Zurich'

    reservation_start_date = TimezoneDateTimeField(
        label=_('From reservation date'),
                timezone=tz,
        fieldset=_('Filter Payments'),
                validators=[StrictOptional()]
    )

    reservation_end_date = TimezoneDateTimeField(
        label=_('To reservation date'),
        timezone=tz,
        fieldset=_('Filter Payments'),
                validators=[StrictOptional()]
    )

    ticket_start_date = TimezoneDateTimeField(
        label=_('Ticket created from date'),
        timezone=tz,
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
                validators=[StrictOptional()]
    )

    ticket_end_date = TimezoneDateTimeField(
        label=_('Ticket created to date'),
        timezone=tz,
        fieldset=_('Filter by Ticket Date'),
        description=_('Filters payments by the creation date of their '
                      'associated ticket.'),
                validators=[StrictOptional()]
    )

    status = SelectField(
        label=_('Status'),
        fieldset=_('Filter Payments'),
        choices=[],  # To be populated in on_request
        default='',
    )

    payment_type = SelectField(
        label=_('Payment Type'),
        fieldset=_('Filter Payments'),
        choices=[],  # To be populated in on_request
        default='',
    )

    def apply_model(self, model: PaymentCollection) -> None:
        """Populate the form fields from the model's filter values."""
        self.reservation_start_date.data = model.reservation_start
        self.reservation_end_date.data = model.reservation_end
        self.status.data = model.status or ''
        self.ticket_start_date.data = model.ticket_start
        self.ticket_end_date.data = model.ticket_end
        self.payment_type.data = model.payment_type or ''

    def update_model(self, model: PaymentCollection) -> None:
        """Update the model's filter values from the form's data."""
        model.reservation_start = self.reservation_start_date.data
        model.reservation_end = self.reservation_end_date.data
        model.status = self.status.data or None
        model.ticket_start = self.ticket_start_date.data
        model.ticket_end = self.ticket_end_date.data
        model.payment_type = self.payment_type.data or None
        # Reset to the first page when filters change
        model.page = 0

    def on_request(self) -> None:
        # Translate choices on request
        self.status.choices = [
            (value, self.request.translate(label))
            for value, label in self.STATUS_CHOICES
        ]
        self.payment_type.choices = [
            (value, self.request.translate(label))
            for value, label in self.PAYMENT_TYPE_CHOICES
        ]
        self.css_class = 'resettable'
