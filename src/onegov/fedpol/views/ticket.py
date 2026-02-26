from __future__ import annotations

from onegov.core.security import Public
from onegov.fedpol import FedpolApp
from onegov.fedpol.layout import TicketChatMessageLayout
from onegov.org.forms import TicketChatMessageForm
from onegov.org.views.ticket import view_ticket_status
from onegov.ticket import Ticket


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fedpol.request import FedpolRequest
    from webob import Response


@FedpolApp.form(
    model=Ticket,
    name='status',
    template='ticket_status.pt',
    permission=Public,
    form=TicketChatMessageForm
)
def fedpol_view_ticket_status(
    self: Ticket,
    request: FedpolRequest,
    form: TicketChatMessageForm
) -> RenderData | Response:
    return view_ticket_status(
        self, request, form, TicketChatMessageLayout(self, request))
