from __future__ import annotations

from onegov.core.orm.types import UUID
from onegov.pay import Invoice
from onegov.user import User
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from decimal import Decimal
    from onegov.activity.models import ActivityInvoiceItem
    from onegov.activity.models import BookingPeriod


class BookingPeriodInvoice(Invoice):
    """ An invoice for all bookings within a period. """

    __mapper_args__ = {
        'polymorphic_identity': 'booking_period'
    }

    #: the period to which this invoice belongs to
    period_id: Column[uuid.UUID] = Column(  # type: ignore[assignment]
        UUID,  # type:ignore[arg-type]
        ForeignKey('periods.id'),
        nullable=True
    )
    period: relationship[BookingPeriod] = relationship(
        'BookingPeriod',
        back_populates='invoices'
    )

    #: the user to which the invoice belongs
    user_id: Column[uuid.UUID] = Column(  # type: ignore[assignment]
        UUID,  # type:ignore[arg-type]
        ForeignKey('users.id'),
        nullable=True
    )
    # FIXME: Do we need this backref? It's across module boundaries, so
    #        not the best for proper module isolation
    user: relationship[User] = relationship(User, backref='invoices')

    if TYPE_CHECKING:
        items: relationship[list[ActivityInvoiceItem]]  # type: ignore[assignment]

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
