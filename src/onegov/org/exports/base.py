from __future__ import annotations

from onegov.org.models import Export
from onegov.town6 import _


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from datetime import datetime
    from onegov.pay import Payment
    from onegov.pay.types import AnyPayableBase
    from onegov.ticket import Ticket


def payment_date_paid(payment: Payment) -> datetime | None:
    if not payment.paid:
        return None
    if payment.source == 'manual':
        # there is not better way to know for now
        return payment.last_change
    if payment.source == 'stripe_connect':
        # meta-property
        return payment.meta.get('payout_date')
    return None


class OrgExport(Export):

    def payment_items_fields(
        self,
        payment: Payment,
        links: Iterable[AnyPayableBase],
        provider_title: str
    ) -> Iterator[tuple[str, Any]]:

        yield _('ID Payment Provider'), payment.remote_id
        yield _('References Payment Provider'), payment.remote_references
        yield _('Status'), _(payment.state.capitalize())
        yield _('Currency'), payment.currency
        yield _('Amount'), payment.amount
        yield _('Net Amount'), round(payment.net_amount, 2)
        yield _('Fee'), round(payment.fee, 2)

        payment_date = payment_date_paid(payment)
        yield _('Payment Provider'), provider_title
        yield _('Date Paid'), payment_date and payment_date.date()
        yield _('References'), [l.payable_reference for l in links]
        yield _('Created Date'), payment.created.date()

    def ticket_item_fields(
        self,
        ticket: Ticket | None
    ) -> Iterator[tuple[str, Any]]:

        ha = ticket and ticket.handler
        yield _('Reference Ticket'), ticket and ticket.number
        yield _('Submitter Email'), ha and ha.email
        yield _('Category Ticket'), ticket and ticket.handler_code
        yield _('Status Ticket'), ticket and _(ticket.state.capitalize())
        yield _('Ticket decided'), ha and (
            _('No') if ha.undecided else _('Yes'))
