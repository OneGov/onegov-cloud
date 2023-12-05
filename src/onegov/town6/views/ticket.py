from onegov.core.security import Public, Private, Secret
from onegov.form import Form
from onegov.org.views.ticket import (
    view_ticket, handle_new_note, handle_edit_note, message_to_submitter,
    view_ticket_status, view_tickets, view_archived_tickets,
    view_pending_tickets, assign_ticket, view_send_to_gever,
    view_delete_all_archived_tickets, delete_ticket)
from onegov.ticket.collection import ArchivedTicketsCollection
from onegov.town6 import TownApp
from onegov.org.forms import TicketNoteForm, TicketAssignmentForm,\
    ExtendedInternalTicketChatMessageForm
from onegov.org.forms import TicketChatMessageForm
from onegov.org.models import TicketNote
from onegov.org.models.resource import FindYourSpotCollection
from onegov.town6 import _
from onegov.ticket import Ticket
from onegov.ticket.collection import TicketCollection
from onegov.town6.layout import (
    FindYourSpotLayout, TicketLayout, TicketNoteLayout,
    TicketChatMessageLayout, TicketsLayout, ArchivedTicketsLayout)


@TownApp.html(model=Ticket, template='ticket.pt', permission=Private)
def town_view_ticket(self, request):
    return view_ticket(self, request, TicketLayout(self, request))


@TownApp.form(
    model=Ticket, name='note', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_new_note(self, request, form):
    return handle_new_note(
        self, request, form, TicketNoteLayout(self, request, _("New Note")))


@TownApp.form(
    model=TicketNote, name='edit', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_edit_note(self, request, form):
    return handle_edit_note(
        self, request, form,
        TicketNoteLayout(self.ticket, request, _("New Note"))
    )


@TownApp.form(
    model=Ticket, name='assign', permission=Private,
    form=TicketAssignmentForm, template='form.pt'
)
def town_assign_ticket(self, request, form):
    return assign_ticket(
        self, request, form, layout=TicketLayout(self, request))


@TownApp.form(model=Ticket, name='message-to-submitter', permission=Private,
              form=ExtendedInternalTicketChatMessageForm, template='form.pt')
def town_message_to_submitter(self, request, form):
    return message_to_submitter(
        self, request, form, TicketChatMessageLayout(self, request))


@TownApp.form(model=Ticket, name='status', template='ticket_status.pt',
              permission=Public, form=TicketChatMessageForm)
def town_view_ticket_status(self, request, form):
    return view_ticket_status(
        self, request, form, TicketChatMessageLayout(self, request))


@TownApp.html(model=TicketCollection, template='tickets.pt',
              permission=Private)
def town_view_tickets(self, request):
    return view_tickets(self, request, TicketsLayout(self, request))


@TownApp.html(model=ArchivedTicketsCollection, template='archived_tickets.pt',
              permission=Private)
def town_view_archived_tickets(self, request):
    return view_archived_tickets(
        self, request, ArchivedTicketsLayout(self, request)
    )


@TownApp.html(model=ArchivedTicketsCollection, name='delete',
              request_method='DELETE', permission=Secret)
def town_view_delete_all_archived_tickets(self, request):
    return view_delete_all_archived_tickets(self, request)


@TownApp.html(model=FindYourSpotCollection, name='tickets',
              template='pending_tickets.pt', permission=Public)
def town_view_pending_tickets(self, request):
    return view_pending_tickets(
        self, request, FindYourSpotLayout(self, request))


@TownApp.html(model=Ticket, name='send-to-gever',
              permission=Private)
def town_send_to_gever(self, request):
    return view_send_to_gever(self, request)


@TownApp.form(
    model=Ticket, permission=Secret, template='form.pt',
    name='delete', form=Form,
)
def town_delete_ticket(self, request, form):
    return delete_ticket(
        self, request, form=form, layout=TicketLayout(self, request))
