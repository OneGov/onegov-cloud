from __future__ import annotations

from onegov.pay import Invoice
from onegov.user import User
from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from decimal import Decimal
    from onegov.activity.models import ActivityInvoiceItem
    from onegov.activity.models import BookingPeriod


class BookingPeriodInvoice(Invoice):
    """ An invoice for all bookings within a period. """

    __mapper_args__ = {
        'polymorphic_identity': 'booking_period'
    }

    #: the period to which this invoice belongs to
    period_id: Mapped[UUID] = mapped_column(
        ForeignKey('periods.id'),
        # NOTE: This is only not nullable for this class and subclasses
        #       in the database it still needs to be nullable, despite
        #       what the type annotation says
        nullable=True
    )
    period: Mapped[BookingPeriod] = relationship(
        'BookingPeriod',
        back_populates='invoices'
    )

    #: the user to which the invoice belongs
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'),
        # NOTE: Same thing here as for period_id
        nullable=True
    )
    # FIXME: Do we need this backref? It's across module boundaries, so
    #        not the best for proper module isolation
    user: Mapped[User] = relationship(User, backref='invoices')

    if TYPE_CHECKING:
        items: Mapped[list[ActivityInvoiceItem]]  # type: ignore[assignment]

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
        attendee_id: UUID | None = None,
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
