from __future__ import annotations

from onegov.core.security import Public, Private, Secret
from onegov.form import Form
from onegov.org.views.ticket import (
    view_ticket, handle_new_note, handle_edit_note, message_to_submitter,
    view_ticket_status, view_tickets, view_archived_tickets,
    view_pending_tickets, assign_ticket, view_send_to_gever,
    view_delete_all_archived_tickets, delete_ticket, change_tag,
    view_my_tickets, view_ticket_invoice, add_invoice_item)
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.town6 import TownApp
from onegov.org.forms import (
    TicketNoteForm, TicketAssignmentForm, TicketChangeTagForm,
    ExtendedInternalTicketChatMessageForm, ManualInvoiceItemForm)
from onegov.org.forms import TicketChatMessageForm
from onegov.org.models import TicketNote
from onegov.org.models.resource import FindYourSpotCollection
from onegov.ticket import Ticket
from onegov.ticket.collection import TicketCollection
from onegov.town6 import _
from onegov.town6.layout import (
    ArchivedTicketsLayout, DefaultLayout, FindYourSpotLayout,
    TicketInvoiceLayout, TicketLayout, TicketNoteLayout,
    TicketChatMessageLayout, TicketsLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=Ticket, template='ticket.pt', permission=Private)
def town_view_ticket(self: Ticket, request: TownRequest) -> RenderData:
    return view_ticket(self, request, TicketLayout(self, request))


@TownApp.form(
    model=Ticket, name='note', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_new_note(
    self: Ticket,
    request: TownRequest,
    form: TicketNoteForm
) -> RenderData | Response:
    return handle_new_note(
        self, request, form, TicketNoteLayout(self, request, _('New Note')))


@TownApp.form(
    model=TicketNote, name='edit', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_edit_note(
    self: TicketNote,
    request: TownRequest,
    form: TicketNoteForm
) -> RenderData | Response:
    assert self.ticket is not None
    return handle_edit_note(
        self, request, form,
        TicketNoteLayout(self.ticket, request, _('New Note'))
    )


@TownApp.form(
    model=Ticket, name='assign', permission=Private,
    form=TicketAssignmentForm, template='form.pt'
)
def town_assign_ticket(
    self: Ticket,
    request: TownRequest,
    form: TicketAssignmentForm
) -> RenderData | Response:
    return assign_ticket(
        self, request, form, layout=TicketLayout(self, request))


@TownApp.form(
    model=Ticket, name='change-tag', permission=Private,
    form=TicketChangeTagForm, template='form.pt'
)
def town_change_tag(
    self: Ticket,
    request: TownRequest,
    form: TicketChangeTagForm,
    layout: TicketLayout | None = None
) -> RenderData | Response:
    return change_tag(
        self, request, form, layout=TicketLayout(self, request))


@TownApp.form(
    model=Ticket, name='message-to-submitter', permission=Private,
    form=ExtendedInternalTicketChatMessageForm, template='form.pt'
)
def town_message_to_submitter(
    self: Ticket,
    request: TownRequest,
    form: ExtendedInternalTicketChatMessageForm
) -> RenderData | Response:
    return message_to_submitter(
        self, request, form, TicketChatMessageLayout(self, request))


@TownApp.form(
    model=Ticket, name='status', template='ticket_status.pt',
    permission=Public, form=TicketChatMessageForm
)
def town_view_ticket_status(
    self: Ticket,
    request: TownRequest,
    form: TicketChatMessageForm
) -> RenderData | Response:
    return view_ticket_status(
        self, request, form, TicketChatMessageLayout(self, request))


@TownApp.html(
    model=Ticket,
    name='invoice',
    template='ticket_invoice.pt',
    permission=Private
)
def town_view_ticket_invoice(self: Ticket, request: TownRequest) -> RenderData:
    return view_ticket_invoice(
        self, request, TicketInvoiceLayout(self, request))


@TownApp.form(
    model=Ticket,
    name='add-invoice-item',
    template='form.pt',
    permission=Private,
    form=ManualInvoiceItemForm
)
def town_add_invoice_item(
    self: Ticket,
    request: TownRequest,
    form: ManualInvoiceItemForm,
    layout: TicketInvoiceLayout | None = None
) -> RenderData | Response:
    return add_invoice_item(
        self, request, form, TicketInvoiceLayout(self, request))


@TownApp.html(
    model=TicketCollection,
    template='tickets.pt',
    permission=Private
)
def town_view_tickets(
    self: TicketCollection,
    request: TownRequest
) -> RenderData:
    return view_tickets(self, request, TicketsLayout(self, request))


@TownApp.html(
    model=ArchivedTicketCollection,
    template='archived_tickets.pt',
    permission=Private
)
def town_view_archived_tickets(
    self: ArchivedTicketCollection,
    request: TownRequest
) -> RenderData:
    return view_archived_tickets(
        self, request, ArchivedTicketsLayout(self, request)
    )


# FIXME: Why are we overriding this view?
@TownApp.html(
    model=ArchivedTicketCollection, name='delete',
    request_method='DELETE', permission=Secret
)
def town_view_delete_all_archived_tickets(
    self: ArchivedTicketCollection,
    request: TownRequest
) -> None:
    return view_delete_all_archived_tickets(self, request)


@TownApp.html(
    model=FindYourSpotCollection, name='tickets',
    template='pending_tickets.pt', permission=Public
)
def town_view_pending_tickets(
    self: FindYourSpotCollection,
    request: TownRequest
) -> RenderData:
    return view_pending_tickets(
        self, request, FindYourSpotLayout(self, request))


# FIXME: Why are we overiding this view?
@TownApp.html(
    model=Ticket,
    name='send-to-gever',
    permission=Private
)
def town_send_to_gever(self: Ticket, request: TownRequest) -> Response:
    return view_send_to_gever(self, request)


@TownApp.form(
    model=Ticket, permission=Secret, template='form.pt',
    name='delete', form=Form,
)
def town_delete_ticket(
    self: Ticket,
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return delete_ticket(
        self, request, form=form, layout=TicketLayout(self, request))


@TownApp.html(
    model=TicketCollection,
    name='my-tickets',
    template='pending_tickets.pt',
    permission=Public
)
def town_view_my_tickets(
    self: TicketCollection,
    request: TownRequest,
    layout: DefaultLayout | None = None
) -> RenderData:
    return view_my_tickets(self, request, DefaultLayout(self, request))
