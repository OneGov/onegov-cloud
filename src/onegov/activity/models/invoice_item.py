from __future__ import annotations

from onegov.core.orm.types import UUID
from onegov.pay import InvoiceItem
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.activity.models import BookingPeriodInvoice
    from sqlalchemy.orm import relationship


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
    attendee_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('attendees.id'),
        nullable=True
    )

    #: organizer (if the item is an activity)
    organizer: Column[str | None] = Column(Text, nullable=True)

    if TYPE_CHECKING:
        invoice: relationship[BookingPeriodInvoice]
