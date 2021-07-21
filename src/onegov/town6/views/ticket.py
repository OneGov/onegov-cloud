from onegov.core.security import Public, Private
from onegov.org.views.ticket import view_ticket, handle_new_note, \
    handle_edit_note, message_to_submitter, view_ticket_status, view_tickets, \
    view_archived_tickets
from onegov.ticket.collection import ArchivedTicketsCollection
from onegov.town6 import TownApp
from onegov.org.forms import TicketNoteForm
from onegov.org.forms import TicketChatMessageForm
from onegov.org.forms import InternalTicketChatMessageForm
from onegov.org.models import TicketNote
from onegov.town6 import _

from onegov.ticket import Ticket, TicketCollection
from onegov.town6.layout import TicketLayout, TicketNoteLayout, \
    TicketChatMessageLayout, TicketsLayout


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


@TownApp.form(model=Ticket, name='message-to-submitter', permission=Private,
              form=InternalTicketChatMessageForm, template='form.pt')
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
    return view_archived_tickets(self, request, TicketsLayout(self, request))
