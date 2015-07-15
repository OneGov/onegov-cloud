import morepath

from onegov.core.security import Public, Private
from onegov.ticket import Ticket, TicketCollection
from onegov.town import _, TownApp
from onegov.town.elements import Link
from onegov.town.mail import send_html_mail
from onegov.town.layout import DefaultLayout, TicketLayout, TicketsLayout
from onegov.user import UserCollection


@TownApp.html(model=Ticket, template='ticket.pt', permission=Private)
def view_ticket(self, request):

    # XXX this is very to do here, much harder when the ticket is updated
    # because there's no good link to the ticket at that point - so when
    # viewing the ticket we commit the sin of possibly changing data in a
    # GET request.
    self.handler.refresh()

    return {
        'title': self.number,
        'layout': TicketLayout(self, request),
        'ticket': self
    }


@TownApp.view(model=Ticket, name='accept', permission=Private)
def accept_ticket(self, request):
    user = UserCollection(request.app.session()).by_username(
        request.identity.userid)

    self.accept_ticket(user)
    request.success(_(u"You have accepted ticket ${number}", mapping={
        'number': self.number
    }))

    return morepath.redirect(request.link(self))


@TownApp.view(model=Ticket, name='close', permission=Private)
def close_ticket(self, request):
    self.close_ticket()

    request.success(_(u"You have closed ticket ${number}", mapping={
        'number': self.number
    }))

    send_html_mail(
        request=request,
        template='mail_ticket_closed.pt',
        subject=_("Your ticket has been closed"),
        receivers=(self.handler.email, ),
        content={
            'model': self
        }
    )

    return morepath.redirect(
        request.link(TicketCollection(request.app.session())))


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

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Ticket Status"), '#')
    ]

    return {
        'title': title,
        'layout': layout,
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
