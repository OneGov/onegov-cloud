import morepath

from onegov.chat import MessageCollection
from onegov.core.utils import normalize_for_url
from onegov.core.custom import json
from onegov.core.orm import as_selectable
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.core.elements import Link, Intercooler, Confirm
from onegov.org.forms import TicketNoteForm
from onegov.org.forms import TicketChatMessageForm
from onegov.org.forms import InternalTicketChatMessageForm
from onegov.org.layout import DefaultLayout
from onegov.org.layout import TicketLayout
from onegov.org.layout import TicketNoteLayout
from onegov.org.layout import TicketsLayout
from onegov.org.layout import TicketChatMessageLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketChatMessage, TicketMessage, TicketNote
from onegov.org.views.message import view_messages_feed
from onegov.ticket import handlers as ticket_handlers
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket.errors import InvalidStateChange
from onegov.user import User, UserCollection
from sqlalchemy import select


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

    if handler.payment:
        handler.payment.sync()

    messages = MessageCollection(
        request.session,
        channel_id=self.number
    )

    stmt = as_selectable("""
        SELECT
            channel_id,    -- Text
            SUM(
                CASE WHEN type = 'ticket_note' THEN
                    1 ELSE 0 END
            ) AS notes,    -- Integer

            SUM(CASE WHEN type = 'ticket_chat' THEN
                    CASE WHEN meta->>'origin' = 'internal' THEN 1
                    ELSE 0
                END ELSE 0 END
            ) AS internal, -- Integer

            SUM(CASE WHEN type = 'ticket_chat' THEN
                    CASE WHEN meta->>'origin' = 'external' THEN 1
                    ELSE 0
                END ELSE 0 END
            ) AS external  -- Integer

        FROM messages
        WHERE type IN ('ticket_note', 'ticket_chat')
        GROUP BY channel_id
    """)

    counts = request.session.execute(
        select(stmt.c).where(stmt.c.channel_id == self.number)).first()

    # if we have a payment, show the payment button
    layout = TicketLayout(self, request)
    payment_button = None

    if self.state == 'pending':
        payment = handler.payment

        if payment and payment.source == 'manual':
            payment_button = manual_payment_button(payment, layout)

        if payment and payment.source == 'stripe_connect':
            payment_button = stripe_payment_button(payment, layout)

    return {
        'title': self.number,
        'layout': layout,
        'ticket': self,
        'summary': summary,
        'deleted': handler.deleted,
        'handler': handler,
        'payment_button': payment_button,
        'counts': counts,
        'feed_data': json.dumps(
            view_messages_feed(messages, request)
        ),
    }


def manual_payment_button(payment, layout):
    if payment.state == 'open':
        return Link(
            text=_("Mark as paid"),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'mark-as-paid'),
            ),
            attrs={'class': 'mark-as-paid button small secondary'},
            traits=(
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url,
                ),
            )
        )

    return Link(
        text=_("Mark as unpaid"),
        url=layout.csrf_protected_url(
            layout.request.link(payment, 'mark-as-unpaid'),
        ),
        attrs={'class': 'mark-as-unpaid button small secondary'},
        traits=(
            Intercooler(
                request_method='POST',
                redirect_after=layout.request.url,
            ),
        )
    )


def stripe_payment_button(payment, layout):
    if payment.state == 'open':
        return Link(
            text=_("Capture Payment"),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'capture')
            ),
            attrs={'class': 'payment-capture button small secondary'},
            traits=(
                Confirm(
                    _("Do you really want capture the payment?"),
                    _(
                        "This usually happens automatically, so there is "
                        "no reason not do capture the payment."
                    ),
                    _("Capture payment"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url
                ),
            )
        )

    if payment.state == 'paid':
        amount = '{:02f} {}'.format(payment.amount, payment.currency)

        return Link(
            text=_("Refund Payment"),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'refund')
            ),
            attrs={'class': 'payment-refund button small secondary'},
            traits=(
                Confirm(
                    _("Do you really want to refund ${amount}?", mapping={
                        'amount': amount
                    }),
                    _("This cannot be undone."),
                    _("Refund ${amount}", mapping={
                        'amount': amount
                    }),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url
                )
            )
        )


def send_email_if_enabled(ticket, request, template, subject):
    email = ticket.snapshot.get('email') or ticket.handler.email

    send_ticket_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(email, ),
        ticket=ticket
    )


def last_internal_message(session, ticket_number):
    messages = MessageCollection(
        session,
        type='ticket_chat',
        channel_id=ticket_number,
        load='newer-first'
    )

    return messages.query()\
        .filter(TicketChatMessage.meta['origin'].astext == 'internal')\
        .first()


def send_chat_message_email_if_enabled(ticket, request, message, origin):
    assert origin in ('internal', 'external')

    messages = MessageCollection(
        request.session,
        channel_id=ticket.number,
        type='ticket_chat')

    if origin == 'internal':

        # if the messages is sent to the outside, we always send an e-mail
        receivers = (ticket.handler.email, )
        reply_to = request.current_username

    else:
        # if the message is sent to the inside, we check the setting on the
        # last message sent to the outside in this ticket - if none exists,
        # we do not notify
        last_internal = last_internal_message(request.session, ticket.number)

        if not last_internal or not last_internal.meta.get('notify'):
            return

        receivers = (last_internal.owner, )
        reply_to = None  # default reply-to given by the application

    # we show the previous messages by going back until we find a message
    # that is not from the same author as the new message (this should usually
    # be the next message, but might include multiple, if someone sent a bunch
    # of messages in succession without getting a reply)
    #
    # note that the resulting thread has to be reversed for the mail template
    def thread():
        messages.older_than = message.id
        messages.load = 'newer-first'

        for m in messages.query():
            yield m

            if m.owner != message.owner:
                break

    send_ticket_mail(
        request=request,
        template='mail_ticket_chat_message.pt',
        subject=_("Your ticket has a new message"),
        content={
            'model': ticket,
            'message': message,
            'thread': tuple(reversed(list(thread()))),
        },
        ticket=ticket,
        receivers=receivers,
        reply_to=reply_to,
        force=True
    )


@OrgApp.form(
    model=Ticket, name='note', permission=Private,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def handle_new_note(self, request, form):

    if form.submitted(request):
        TicketNote.create(self, request, form.text.data, form.file.create())
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
        form.populate_obj(self)
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
                subject=_("Your ticket has been reopened")
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


@OrgApp.form(model=Ticket, name='message-to-submitter', permission=Private,
             form=InternalTicketChatMessageForm, template='form.pt')
def message_to_submitter(self, request, form):
    recipient = self.snapshot.get('email') or self.handler.email

    if form.submitted(request):
        if self.state == 'closed':
            request.alert(_("The ticket has already been closed"))
        else:
            message = TicketChatMessage.create(
                self, request,
                text=form.text.data,
                owner=request.current_username,
                recipient=recipient,
                notify=form.notify.data,
                origin='internal')

            send_chat_message_email_if_enabled(
                self, request, message, origin='internal')

            request.success(_("Your message has been sent"))
            return morepath.redirect(request.link(self))
    elif not request.POST:
        # show the same notification setting as was selected with the
        # last internal message - otherwise default to False
        last_internal = last_internal_message(request.session, self.number)

        if last_internal:
            form.notify.data = last_internal.meta.get('notify', False)
        else:
            form.notify.data = False

    return {
        'title': _("New Message"),
        'layout': TicketChatMessageLayout(self, request),
        'form': form,
        'helptext': _(
            "The following message will be sent to ${address} and it will be "
            "recorded for future reference.", mapping={
                'address': recipient
            }
        )
    }


@OrgApp.form(model=Ticket, name='status', template='ticket_status.pt',
             permission=Public, form=TicketChatMessageForm)
def view_ticket_status(self, request, form):

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

    if form.submitted(request):

        if self.state == 'closed':
            request.alert(_("The ticket has already been closed"))
        else:
            message = TicketChatMessage.create(
                self, request,
                text=form.text.data,
                owner=self.handler.email,
                origin='external')

            send_chat_message_email_if_enabled(
                self, request, message, origin='external')

            request.success(_("Your message has been received"))
            return morepath.redirect(request.link(self, 'status'))

    messages = MessageCollection(
        request.session,
        channel_id=self.number,
        type=request.app.settings.org.public_ticket_messages
    )

    return {
        'title': title,
        'layout': layout,
        'ticket': self,
        'feed_data': messages and json.dumps(
            view_messages_feed(messages, request)
        ) or None,
        'form': form
    }


@OrgApp.html(model=TicketCollection, template='tickets.pt',
             permission=Private)
def view_tickets(self, request):
    query = as_selectable("""
        SELECT
            handler_code,                         -- Text
            ARRAY_AGG(DISTINCT "group") AS groups -- ARRAY(Text)
        FROM tickets GROUP BY handler_code
    """)

    groups = {
        r.handler_code: r.groups
        for r in request.session.execute(select(query.c))
    }

    for handler in groups:
        groups[handler].sort(key=lambda g: normalize_for_url(g))

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
                attrs={'class': 'ticket-filter-' + id}
            )

    def get_handlers():
        nonlocal groups

        handlers = []

        for key, handler in ticket_handlers.registry.items():
            if key in groups:
                handlers.append(
                    (key, request.translate(handler.handler_title)))

        handlers.sort(key=lambda item: item[1])
        handlers.insert(0, ('ALL', _("All Tickets")))

        for id, text in handlers:
            grouplinks = id != 'ALL' and tuple(get_groups(id))
            parent = grouplinks and len(grouplinks) > 1
            classes = parent and (id + '-link', 'is-parent') or (id + '-link',)

            yield Link(
                text=text,
                url=request.link(self.for_handler(id).for_group(None)),
                active=self.handler == id and self.group is None,
                attrs={'class': ' '.join(classes)}
            )

            if parent:
                yield from grouplinks

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

        for group in groups[handler]:
            yield Link(
                text=group,
                url=request.link(base.for_group(group)),
                active=self.handler == handler and self.group == group,
                attrs={'class': ' '.join(
                    (handler + '-sub-link', 'ticket-group-filter')
                )}
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
