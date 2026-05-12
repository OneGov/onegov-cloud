from __future__ import annotations

from onegov.core.security import Personal
from onegov.org.views.ticket import (
    view_ticket as org_view_ticket,
    view_tickets as org_view_tickets
)
from onegov.town6.layout import TicketsLayout
from onegov.ticket import Ticket
from onegov.ticket.collection import TicketCollection
from onegov.translator_directory.app import TranslatorDirectoryApp
from onegov.translator_directory.layout import TicketLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest

"""
Permissions diverge from org in the following:
For time report tickets, editors have access.
"""


@TranslatorDirectoryApp.html(
    model=Ticket, template='ticket.pt', permission=Personal
)
def translator_directory_view_ticket(
    self: Ticket, request: TranslatorAppRequest
) -> RenderData:
    return org_view_ticket(self, request, TicketLayout(self, request))


@TranslatorDirectoryApp.html(
    model=TicketCollection, template='tickets.pt', permission=Personal
)
def translator_directory_view_tickets(
    self: TicketCollection,
    request: TranslatorAppRequest,
    layout: TicketsLayout | None = None,
) -> RenderData:
    return org_view_tickets(self, request, TicketsLayout(self, request))
