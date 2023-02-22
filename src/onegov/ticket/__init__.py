from onegov.ticket.handler import Handler, HandlerRegistry
handlers = HandlerRegistry()  # noqa$

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.ticket')  # noqa

from onegov.ticket.model import Ticket
from onegov.ticket.model import TicketPermission
from onegov.ticket.collection import TicketCollection


__all__ = [
    'Handler',
    'handlers',
    'Ticket',
    'TicketCollection',
    'TicketPermission'
]
