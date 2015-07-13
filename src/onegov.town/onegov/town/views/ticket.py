from onegov.core.security import Public, Private
from onegov.ticket import Ticket, TicketCollection
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout, TicketLayout, TicketsLayout


@TownApp.html(model=Ticket, template='ticket.pt', permission=Private)
def view_ticket(self, request):

    return {
        'title': self.number,
        'layout': TicketLayout(self, request),
        'ticket': self
    }


@TownApp.html(model=Ticket, name='status', template='ticket_status.pt',
              permission=Public)
def view_ticket_status(self, request):

    if self.state == 'open':
        title = _("Your request has been submitted")
    elif self.state == 'pending':
        title = _("Your request is currently pending")
    elif self.state == 'closed':
        title = _("Your request has been processed")
    else:
        raise NotImplementedError

    return {
        'title': title,
        'layout': DefaultLayout(self, request),
        'ticket': self
    }


@TownApp.html(model=TicketCollection, template='tickets.pt',
              permission=Private)
def view_tickets(self, request):

    def get_filters():
        states = (
            ('open', _("Open")),
            ('pending', _("Pending")),
            ('closed', _("Closed"))
        )

        for id, text in states:
            yield Link(
                text=text,
                url=request.link(self.for_state(id)),
                active=self.state == id
            )

    if self.state == 'open':
        tickets_title = _("Open Tickets")
    elif self.state == 'pending':
        tickets_title = _("Pending Tickets")
    elif self.state == 'closed':
        tickets_title = _("Closed Tickets")
    else:
        raise NotImplementedError

    return {
        'title': _("Tickets"),
        'layout': TicketsLayout(self, request),
        'tickets': self.batch,
        'filters': tuple(get_filters()),
        'tickets_title': tickets_title,
    }
