from onegov.ticket.handler import Handler, HandlerRegistry
handlers = HandlerRegistry()  # noqa

from onegov.ticket.model import Ticket
from onegov.ticket.collection import TicketCollection


__all__ = [
    'Handler',
    'handlers',
    'Ticket',
    'TicketCollection'
]
