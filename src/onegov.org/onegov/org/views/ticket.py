import morepath

from onegov.core.security import Public, Private
from onegov.org.elements import Link
from onegov.org.layout import DefaultLayout, TicketLayout, TicketsLayout
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket import handlers as ticket_handlers
from onegov.ticket.errors import InvalidStateChange
from onegov.org import _, OrgApp
from onegov.org.mail import send_html_mail
from onegov.user import UserCollection


@OrgApp.html(model=Ticket, template='ticket.pt', permission=Private)
def view_ticket(self, request):

    handler = self.handler

    if handler.deleted:
        summary = self.snapshot.get('summary')
    else:
        # XXX this is very to do here, much harder when the ticket is updated
        # because there's no good link to the ticket at that point - so when
        # viewing the ticket we commit the sin of possibly changing data in a
        # GET request.
        handler.refresh()
        summary = handler.get_summary(request)

    return {
        'title': self.number,
        'layout': TicketLayout(self, request),
        'ticket': self,
        'summary': summary,
        'deleted': handler.deleted,
        'handler': handler
    }


@OrgApp.view(model=Ticket, name='accept', permission=Private)
def accept_ticket(self, request):
    user = UserCollection(request.app.session()).by_username(
        request.identity.userid)

    try:
        self.accept_ticket(user)
    except InvalidStateChange:
        request.alert(_("The ticket cannot be accepted because it's not open"))
    else:
        request.success(_("You have accepted ticket ${number}", mapping={
            'number': self.number
        }))

    request.app.update_ticket_count()

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='close', permission=Private)
def close_ticket(self, request):

    try:
        self.close_ticket()
    except InvalidStateChange:
        request.alert(
            _("The ticket cannot be closed because it's not pending")
        )
    else:
        request.success(_("You have closed ticket ${number}", mapping={
            'number': self.number
        }))

    email = self.snapshot.get('email') or self.handler.email

    send_html_mail(
        request=request,
        template='mail_ticket_closed.pt',
        subject=_("Your ticket has been closed"),
        receivers=(email, ),
        content={
            'model': self
        }
    )

    request.app.update_ticket_count()

    return morepath.redirect(
        request.link(TicketCollection(request.app.session())))


@OrgApp.view(model=Ticket, name='reopen', permission=Private)
def reopen_ticket(self, request):
    user = UserCollection(request.app.session()).by_username(
        request.identity.userid)

    try:
        self.reopen_ticket(user)
    except InvalidStateChange:
        request.alert(
            _("The ticket cannot be re-opened because it's not closed.")
        )
    else:
        request.success(_("You have reopened ticket ${number}", mapping={
            'number': self.number
        }))

    email = self.snapshot.get('email') or self.handler.email

    send_html_mail(
        request=request,
        template='mail_ticket_reopened.pt',
        subject=_("Your ticket has been reopened"),
        receivers=(email, ),
        content={
            'model': self
        }
    )

    request.app.update_ticket_count()

    return morepath.redirect(request.link(self))


@OrgApp.html(model=Ticket, name='status', template='ticket_status.pt',
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


@OrgApp.html(model=TicketCollection, template='tickets.pt',
             permission=Private)
def view_tickets(self, request):

    def get_filters():
        states = (
            ('open', _("Open")),
            ('pending', _("Pending")),
            ('closed', _("Closed")),
            ('all', _("All"))
        )

        for id, text in states:
            yield Link(
                text=text,
                url=request.link(self.for_state(id)),
                active=self.state == id,
                classes=('ticket-filter-' + id, )
            )

    def get_handlers():

        handlers = []

        for key, handler in ticket_handlers.registry.items():
            handlers.append((key, request.translate(handler.handler_title)))

        handlers.sort(key=lambda item: item[1])
        handlers.insert(0, ('ALL', _("All")))

        for id, text in handlers:
            groups = id != 'ALL' and tuple(get_groups(id))
            parent = groups and len(groups) > 1
            classes = parent and (id + '-link', 'is-parent') or (id + '-link',)

            yield Link(
                text=text,
                url=request.link(self.for_handler(id).for_group(None)),
                active=self.handler == id and self.group is None,
                classes=classes
            )

            if parent:
                yield from groups

    def get_groups(handler):
        base = self.for_handler(handler)

        for group in self.available_groups(handler):
            yield Link(
                text=group,
                url=request.link(base.for_group(group)),
                active=self.handler == handler and self.group == group,
                classes=(handler + '-sub-link', 'ticket-group-filter')
            )

    if self.state == 'open':
        tickets_title = _("Open Tickets")
    elif self.state == 'pending':
        tickets_title = _("Pending Tickets")
    elif self.state == 'closed':
        tickets_title = _("Closed Tickets")
    elif self.state == 'all':
        tickets_title = _("All Tickets")
    else:
        raise NotImplementedError

    return {
        'title': _("Tickets"),
        'layout': TicketsLayout(self, request),
        'tickets': self.batch,
        'filters': tuple(get_filters()),
        'handlers': tuple(get_handlers()),
        'tickets_title': tickets_title,
        'tickets_state': self.state,
        'has_handler_filter': self.handler != 'ALL'
    }
