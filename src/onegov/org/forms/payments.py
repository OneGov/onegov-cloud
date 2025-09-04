from __future__ import annotations

from onegov.form.core import Form
from onegov.form.fields import TranslatedSelectField, TimezoneDateTimeField
from onegov.form.validators import StrictOptional
from onegov.org import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay import PaymentCollection
    from onegov.ticket import TicketInvoiceCollection


def coerce_optional_bool(choice: str | bool | None) -> bool | None:
    if isinstance(choice, str):
        match choice.lower():
            case 'true':
                return True
            case 'false':
                return False
            case _:
                return None
    return choice


class TicketInvoiceSearchForm(Form):

    tz = 'Europe/Zurich'
    css_class = 'resettable'

    invoiced = TranslatedSelectField(
        label=_('Status'),
        fieldset=_('Filter Invoices'),
        choices=[
            ('None', _('All')),
            ('False', _('Uninvoiced')),
            ('True', _('Invoiced')),
        ],
        coerce=coerce_optional_bool,
        default=None,
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

    reservation_start_date = TimezoneDateTimeField(
        label=_('From reservation date'),
        timezone=tz,
        fieldset=_('Filter by Reservation Date'),
        validators=[StrictOptional()]
    )

    reservation_end_date = TimezoneDateTimeField(
        label=_('To reservation date'),
        timezone=tz,
        fieldset=_('Filter by Reservation Date'),
        validators=[StrictOptional()]
    )

    def apply_model(self, model: TicketInvoiceCollection) -> None:
        """Populate the form fields from the model's filter values."""
        self.invoiced.data = model.invoiced
        self.ticket_start_date.data = model.ticket_start
        self.ticket_end_date.data = model.ticket_end
        self.reservation_start_date.data = model.reservation_start
        self.reservation_end_date.data = model.reservation_end

    def update_model(self, model: TicketInvoiceCollection) -> None:
        """Update the model's filter values from the form's data."""
        model.invoiced = self.invoiced.data
        model.ticket_start = self.ticket_start_date.data
        model.ticket_end = self.ticket_end_date.data
        model.reservation_start = self.reservation_start_date.data
        model.reservation_end = self.reservation_end_date.data
        # Reset to the first page when filters change
        model.page = 0


class PaymentSearchForm(Form):

    tz = 'Europe/Zurich'
    css_class = 'resettable'

    status = TranslatedSelectField(
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

    payment_type = TranslatedSelectField(
        label=_('Payment Type'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('manual', _('Manual')),
            ('provider', _('Payment Provider'))
        ],
        default='',
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

    reservation_start_date = TimezoneDateTimeField(
        label=_('From reservation date'),
                timezone=tz,
        fieldset=_('Filter by Reservation Date'),
                validators=[StrictOptional()]
    )

    reservation_end_date = TimezoneDateTimeField(
        label=_('To reservation date'),
        timezone=tz,
        fieldset=_('Filter by Reservation Date'),
                validators=[StrictOptional()]
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
