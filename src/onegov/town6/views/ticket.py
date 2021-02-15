from onegov.core.security import Public, Private
from onegov.org.views.ticket import view_ticket, handle_new_note, \
    handle_edit_note, message_to_submitter, view_ticket_status, view_tickets
from onegov.town6 import TownApp
from onegov.org.forms import TicketNoteForm
from onegov.org.forms import TicketChatMessageForm
from onegov.org.forms import InternalTicketChatMessageForm
from onegov.org.models import TicketNote

from onegov.ticket import Ticket, TicketCollection


@TownApp.html(model=Ticket, template='ticket.pt', permission=Private)
def town_view_ticket(self, request):
    return view_ticket(self, request)


@TownApp.form(
    model=Ticket, name='note', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_new_note(self, request, form):
    return handle_new_note(self, request, form)


@TownApp.form(
    model=TicketNote, name='edit', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def town_handle_edit_note(self, request, form):
    return handle_edit_note(self, request, form)


@TownApp.form(model=Ticket, name='message-to-submitter', permission=Private,
              form=InternalTicketChatMessageForm, template='form.pt')
def town_message_to_submitter(self, request, form):
    return message_to_submitter(self, request, form)


@TownApp.form(model=Ticket, name='status', template='ticket_status.pt',
              permission=Public, form=TicketChatMessageForm)
def town_view_ticket_status(self, request, form):
    return view_ticket_status(self, request, form)


@TownApp.html(model=TicketCollection, template='tickets.pt',
              permission=Private)
def town_view_tickets(self, request):
    return view_tickets(self, request)
