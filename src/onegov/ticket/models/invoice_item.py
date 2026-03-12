from __future__ import annotations

from onegov.pay import InvoiceItem
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket.models import TicketInvoice


class TicketInvoiceItem(InvoiceItem):
    """ An invoice item related to a ticket. """

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    #: the submission, if the item is related to a form submission
    submission_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('submissions.id'),
        index=True
    )

    # NOTE: We would like to use ForeignKey here as well, however due to
    #       the different base classes between libres and onegov, we can't
    #       have a foreign key constraint between those two worlds (at least
    #       not without considerable additional effort)
    #: the reservation if the item is related to a reservation
    reservation_id: Mapped[int | None] = mapped_column(index=True)

    if TYPE_CHECKING:
        invoice: Mapped[TicketInvoice]
