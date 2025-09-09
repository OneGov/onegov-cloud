from __future__ import annotations

from onegov.pay import Invoice
from onegov.user import User
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable
    from decimal import Decimal
    from onegov.activity.models import ActivityInvoiceItem
    from onegov.activity.models import BookingPeriod
    from sqlalchemy import Column


class BookingPeriodInvoice(Invoice):
    """ An invoice for all bookings within a period. """

    __mapper_args__ = {
        'polymorphic_identity': 'booking_period'
    }

    #: the period to which this invoice belongs to
    period_id: Column[uuid.UUID]
    period: relationship[BookingPeriod] = relationship(
        'BookingPeriod',
        back_populates='invoices'
    )

    #: the user to which the invoice belongs
    user_id: Column[uuid.UUID]
    # FIXME: Do we need this backref? It's across module boundaries, so
    #        not the best for proper module isolation
    user: relationship[User] = relationship(User, backref='invoices')

    if TYPE_CHECKING:
        items: relationship[list[ActivityInvoiceItem]]  # type: ignore[assignment]

    @property
    def has_donation(self) -> bool:
        for item in self.items:
            if item.group == 'donation':
                return True
        return False

    def add(
        self,
        group: str,
        text: str,
        unit: Decimal,
        quantity: Decimal,
        *,
        organizer: str = '',
        attendee_id: uuid.UUID | None = None,
        flush: bool = True,
        **kwargs: Any  # FIXME: type safety for optional arguments
    ) -> ActivityInvoiceItem:
        return super().add(  # type: ignore[return-value]
            type='activity',
            group=group,
            text=text,
            unit=unit,
            quantity=quantity,
            organizer=organizer,
            attendee_id=attendee_id,
            flush=flush,
            **kwargs
        )

    @hybrid_property
    def discourage_changes(self) -> bool:
        return self.discourage_changes_for_items(self.items)

    @hybrid_property
    def disable_changes(self) -> bool:
        return self.disable_changes_for_items(self.items)

    @hybrid_property
    def has_online_payments(self) -> bool:
        return self.has_online_payments_for_items(self.items)

    def discourage_changes_for_items(
        self,
        items: Iterable[ActivityInvoiceItem]
    ) -> bool:
        for item in items:
            if item.source == 'xml':
                return True

        return False

    def disable_changes_for_items(
        self,
        items: Iterable[ActivityInvoiceItem]
    ) -> bool:
        for item in items:
            if not item.source:
                continue

            if item.source == 'xml':
                continue

            states = {p.state for p in item.payments}

            if 'open' in states or 'paid' in states:
                return True
        return False

    def has_online_payments_for_items(
        self,
        items: Iterable[ActivityInvoiceItem]
    ) -> bool:
        for item in items:
            if not item.source or item.source == 'xml':
                continue

            return True
        return False
