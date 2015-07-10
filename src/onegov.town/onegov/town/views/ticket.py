from onegov.core.security import Public, Private
from onegov.ticket import Ticket, TicketCollection
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout, TicketsLayout
from sqlalchemy import desc
from sqlalchemy.orm import joinedload, undefer


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

    # TODO add pagination
    query = TicketCollection(request.app.session()).query()
    query = query.order_by(desc(Ticket.created))
    query = query.options(joinedload(Ticket.user))
    query = query.options(undefer(Ticket.created))

    # TODO add to the collection model?
    state = request.params.get('state', 'open')
    state = state in {'open', 'pending', 'closed'} and state or 'open'

    query = query.filter(Ticket.state == state)

    base = request.link(self)
    filters = [
        Link(_("Open"), base + '?state=open', active=state == 'open'),
        Link(_("Pending"), base + '?state=pending', active=state == 'pending'),
        Link(_("Closed"), base + '?state=closed', active=state == 'closed'),
    ]

    if state == 'open':
        tickets_title = _("Open Tickets")
    elif state == 'pending':
        tickets_title = _("Pending Tickets")
    elif state == 'closed':
        tickets_title = _("Closed Tickets")

    return {
        'title': _("Tickets"),
        'layout': TicketsLayout(self, request),
        'tickets': query.all(),
        'filters': filters,
        'tickets_title': tickets_title
    }
