from __future__ import annotations

from onegov.core.orm.types import UUID
from onegov.pay import InvoiceItem
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.ticket.models import TicketInvoice
    from sqlalchemy.orm import relationship


class TicketInvoiceItem(InvoiceItem):
    """ An invoice item related to a ticket. """

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    #: the submission, if the item is related to a form submission
    submission_id: Column[uuid.UUID | None] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('submissions.id'),
        nullable=True,
        index=True
    )

    # NOTE: We would like to use ForeignKey here as well, however due to
    #       the different base classes between libres and onegov, we can't
    #       have a foreign key constraint between those two worlds (at least
    #       not without considerable additional effort)
    #: the reservation if the item is related to a reservation
    reservation_id: Column[int | None] = Column(
        Integer(),
        nullable=True,
        index=True
    )

    if TYPE_CHECKING:
        invoice: relationship[TicketInvoice]
