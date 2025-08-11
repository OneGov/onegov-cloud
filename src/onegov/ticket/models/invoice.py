from __future__ import annotations

from decimal import Decimal
from onegov.pay import Invoice
from sqlalchemy.orm import relationship


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.ticket import Ticket, TicketInvoiceItem


class TicketInvoice(Invoice):
    """ An invoice belonging to a specific ticket. """

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    # NOTE: Currently each invoice belongs to a single ticket
    #       but there are some potential use-cases for merging
    #       the invoices of multiple related tickets, so this
    #       might become a list later on.
    #: the ticket to which this invoice belongs to
    ticket: relationship[Ticket | None] = relationship(
        'Ticket',
        back_populates='invoice',
        uselist=False
    )

    if TYPE_CHECKING:
        items: relationship[list[TicketInvoiceItem]]  # type: ignore[assignment]

    def add(
        self,
        group: str,
        text: str,
        unit: Decimal,
        quantity: Decimal = Decimal('1'),
        *,
        submission_id: uuid.UUID | None = None,
        reservation_id: int | None = None,
        family: str | None = None,
        vat_rate: Decimal | None = None,
        tid: str | None = None,
        source: str | None = None,
        flush: bool = True,
        **kwargs: Any,
    ) -> TicketInvoiceItem:
        return super().add(  # type: ignore[return-value]
            type='ticket',
            group=group,
            family=family,
            text=text,
            tid=tid,
            source=source,
            unit=unit,
            quantity=quantity,
            vat_rate=vat_rate,
            submission_id=submission_id,
            reservation_id=reservation_id,
            flush=flush,
        )
