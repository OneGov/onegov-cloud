from __future__ import annotations

from onegov.pay import InvoiceItem
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import BookingPeriodInvoice


class ActivityInvoiceItem(InvoiceItem):
    """
    An invoice item related to an activity.

    Could also just be a donation or manual invoice item unrelated
    to a specific activity.
    """

    __mapper_args__ = {
        'polymorphic_identity': 'activity'
    }

    #: the attendee, if the item is connected to an attendee
    attendee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('attendees.id')
    )

    #: organizer (if the item is an activity)
    organizer: Mapped[str | None]

    if TYPE_CHECKING:
        invoice: Mapped[BookingPeriodInvoice]
