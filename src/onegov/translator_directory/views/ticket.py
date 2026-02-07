from __future__ import annotations

from onegov.core.security import Personal
from onegov.org.views.ticket import view_ticket
from onegov.ticket import Ticket
from onegov.translator_directory.app import TranslatorDirectoryApp
from onegov.translator_directory.layout import TicketLayout


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest


@TranslatorDirectoryApp.html(
    model=Ticket, template='ticket.pt', permission=Personal
)
def translator_directory_view_ticket(
    self: Ticket, request: TranslatorAppRequest
) -> RenderData:
    return view_ticket(self, request, TicketLayout(self, request))
