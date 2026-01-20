from __future__ import annotations

from onegov.org import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay.types import PaymentState
    from onegov.ticket.collection import ExtendedTicketState


TICKET_STATES: dict[ExtendedTicketState, str] = {
    'open': _('Open'),
    'pending': _('Pending'),
    'closed': _('Closed'),
    'archived': _('Archived'),
    'all': _('All'),
}

INVOICE_GROUPS = {
    'reservation': _('Reservations'),
    'submission': _('Submission'),
    'form': _('Selected Options'),
    'manual': _('Discounts / Surcharges'),
    'migration': _('Lump sum'),
}

PAYMENT_STATES: dict[PaymentState, str] = {
    'open': TICKET_STATES['open'],
    'paid': _('Paid'),
    'failed': _('Failed'),
    'cancelled': _('Refunded'),
    'invoiced': _('Invoiced'),
}

PAYMENT_SOURCES = {
    'manual': _('Manual'),
    'datatrans': _('Datatrans'),
    'stripe_connect': _('Stripe Connect'),
    'worldline_saferpay': _('Worldline Saferpay'),
}
