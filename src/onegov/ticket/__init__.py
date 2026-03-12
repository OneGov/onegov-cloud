from __future__ import annotations

from onegov.ticket.handler import Handler, HandlerRegistry
handlers = HandlerRegistry()

from onegov.ticket.models import Ticket
from onegov.ticket.models import TicketInvoice
from onegov.ticket.models import TicketInvoiceItem
from onegov.ticket.models import TicketPermission
from onegov.ticket.collection import TicketCollection
from onegov.ticket.collection import TicketInvoiceCollection


__all__ = (
    'Handler',
    'handlers',
    'Ticket',
    'TicketCollection',
    'TicketInvoice',
    'TicketInvoiceCollection',
    'TicketInvoiceItem',
    'TicketPermission',
)
