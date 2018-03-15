import morepath

from onegov.chat import MessageCollection
from onegov.core.custom import json
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import TicketNoteForm
from onegov.org.layout import DefaultLayout
from onegov.org.layout import TicketLayout
from onegov.org.layout import TicketNoteLayout
from onegov.org.layout import TicketsLayout
from onegov.org.mail import send_transactional_html_mail
from onegov.org.models import TicketMessage, TicketNote
from onegov.org.views.message import view_messages_feed
from onegov.ticket import handlers as ticket_handlers
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket.errors import InvalidStateChange
from onegov.user import User, UserCollection


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

    if self.handler.payment:
        self.handler.payment.sync()

    messages = MessageCollection(
        request.session,
        channel_id=self.number
    )

    return {
        'title': self.number,
        'layout': TicketLayout(self, request),
        'ticket': self,
        'summary': summary,
        'deleted': handler.deleted,
        'handler': handler,
        'feed_data': json.dumps(
            view_messages_feed(messages, request)
        ),
    }


def send_email_if_enabled(ticket, request, template, subject):
    email = ticket.snapshot.get('email') or ticket.handler.email

    # do not send an e-mail if the recipient is the current logged in user
    if email == request.current_username:
        return

    # do not send an e-mail if the ticket is muted
    if ticket.muted:
        return

    send_transactional_html_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(email, ),
        content={
            'model': ticket
        }
    )


@OrgApp.form(
    model=Ticket, name='note', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def handle_new_note(self, request, form):

    if form.submitted(request):
        TicketNote.create(self, request, form.text.data)
        request.success(_("Your note was added"))
        return request.redirect(request.link(self))

    return {
        'title': _("New Note"),
        'layout': TicketNoteLayout(self, request, _("New Note")),
        'form': form,
        'hint': 'default'
    }


@OrgApp.view(model=TicketNote, permission=Private)
def view_ticket_note(self, request):
    return request.redirect(request.link(self.ticket))


@OrgApp.view(model=TicketNote, permission=Private, request_method='DELETE')
def delete_ticket_note(self, request):
    request.assert_valid_csrf_token()

    # force a change of the ticket to make sure that it gets reindexed
    self.ticket.force_update()

    request.session.delete(self)
    request.success(_("The note was deleted"))


@OrgApp.form(
    model=TicketNote, name='edit', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def handle_edit_note(self, request, form):
    if form.submitted(request):
        self.text = form.text.data
        self.owner = request.current_username

        # force a change of the ticket to make sure that it gets reindexed
        self.ticket.force_update()

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.ticket))

    elif not request.POST:
        form.process(obj=self)

    return {
        'title': _("Edit Note"),
        'layout': TicketNoteLayout(self.ticket, request, _("New Note")),
        'form': form,
        'hint': self.owner != request.current_username and 'owner'
    }


@OrgApp.view(model=Ticket, name='accept', permission=Private)
def accept_ticket(self, request):
    user = UserCollection(request.session).by_username(
        request.identity.userid)

    was_pending = self.state == 'open'

    try:
        self.accept_ticket(user)
    except InvalidStateChange:
        request.alert(_("The ticket cannot be accepted because it's not open"))
    else:
        if was_pending:
            TicketMessage.create(self, request, 'accepted')
            request.success(_("You have accepted ticket ${number}", mapping={
                'number': self.number
            }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='close', permission=Private)
def close_ticket(self, request):

    was_pending = self.state == 'pending'

    try:
        self.close_ticket()
    except InvalidStateChange:
        request.alert(
            _("The ticket cannot be closed because it's not pending")
        )
    else:
        if was_pending:
            TicketMessage.create(self, request, 'closed')
            request.success(_("You have closed ticket ${number}", mapping={
                'number': self.number
            }))

            send_email_if_enabled(
                ticket=self,
                request=request,
                template='mail_ticket_closed.pt',
                subject=_("Your ticket has been closed")
            )

    return morepath.redirect(
        request.link(TicketCollection(request.session)))


@OrgApp.view(model=Ticket, name='reopen', permission=Private)
def reopen_ticket(self, request):
    user = UserCollection(request.session).by_username(
        request.identity.userid)

    was_closed = self.state == 'closed'

    try:
        self.reopen_ticket(user)
    except InvalidStateChange:
        request.alert(
            _("The ticket cannot be re-opened because it's not closed")
        )
    else:
        if was_closed:
            TicketMessage.create(self, request, 'reopened')
            request.success(_("You have reopened ticket ${number}", mapping={
                'number': self.number
            }))

            send_email_if_enabled(
                ticket=self,
                request=request,
                template='mail_ticket_reopened.pt',
                subject=_("Your ticket has been repoened")
            )

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='mute', permission=Private)
def mute_ticket(self, request):
    self.muted = True

    TicketMessage.create(self, request, 'muted')
    request.success(
        _("You have disabled e-mails for ticket ${number}", mapping={
            'number': self.number
        }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='unmute', permission=Private)
def unmute_ticket(self, request):
    self.muted = False

    TicketMessage.create(self, request, 'unmuted')
    request.success(
        _("You have enabled e-mails for ticket ${number}", mapping={
            'number': self.number
        }))

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
        handlers.insert(0, ('ALL', _("All Tickets")))

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

    def get_owners():

        users = UserCollection(request.session)
        users = users.by_roles(*request.app.settings.org.ticket_manager_roles)
        users = users.order_by(User.title)

        yield Link(
            text=_("All Users"),
            url=request.link(self.for_owner('*')),
            active=self.owner == '*'
        )

        for user in users:
            yield Link(
                text=user.title,
                url=request.link(self.for_owner(user.id)),
                active=self.owner == user.id.hex,
                model=user
            )

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

    handlers = tuple(get_handlers())
    owners = tuple(get_owners())
    filters = tuple(get_filters())

    handler = next((h for h in handlers if h.active), None)
    owner = next((o for o in owners if o.active), None)

    return {
        'title': _("Tickets"),
        'layout': TicketsLayout(self, request),
        'tickets': self.batch,
        'filters': filters,
        'handlers': handlers,
        'owners': owners,
        'tickets_title': tickets_title,
        'tickets_state': self.state,
        'has_handler_filter': self.handler != 'ALL',
        'has_owner_filter': self.owner != '*',
        'handler': handler,
        'owner': owner
    }
