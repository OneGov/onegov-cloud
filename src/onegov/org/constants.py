from onegov.org import _

TICKET_STATES = {
    'open': _("Open"),
    'pending': _("Pending"),
    'closed': _("Closed"),
    'archived': _("Archived"),
    'all': _("All")
}

PAYMENT_STATES = {
    'open': TICKET_STATES['open'],
    'paid': _("Paid"),
    'failed': _("Failed"),
    'cancelled': _("Refunded")
}

PAYMENT_SOURCES = {
    'manual': _('Manual'),
    'stripe_connect': _("Stripe Connect")
}
