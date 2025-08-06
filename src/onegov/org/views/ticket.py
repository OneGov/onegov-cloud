from __future__ import annotations

import morepath
import os
import zipfile

from datetime import date
from io import BytesIO
from itertools import groupby
from markupsafe import Markup
from morepath import Response
from onegov.chat import Message, MessageCollection
from onegov.core.custom import json
from onegov.core.elements import Link, Intercooler, Confirm
from onegov.core.html import html_to_text
from onegov.core.mail import Attachment
from onegov.core.orm import as_selectable
from onegov.core.security import Public, Personal, Private, Secret
from onegov.core.templates import render_template
from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org import _, OrgApp
from onegov.org.constants import TICKET_STATES
from onegov.org.forms import ExtendedInternalTicketChatMessageForm
from onegov.org.forms import ManualInvoiceItemForm
from onegov.org.forms import TicketAssignmentForm
from onegov.org.forms import TicketChangeTagForm
from onegov.org.forms import TicketChatMessageForm
from onegov.org.forms import TicketNoteForm
from onegov.org.layout import (
    FindYourSpotLayout, DefaultMailLayout, ArchivedTicketsLayout)
from onegov.org.layout import DefaultLayout
from onegov.org.layout import TicketChatMessageLayout
from onegov.org.layout import TicketInvoiceLayout
from onegov.org.layout import TicketLayout
from onegov.org.layout import TicketNoteLayout
from onegov.org.layout import TicketsLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import (
    CitizenDashboard, TicketChatMessage, TicketMessage, TicketNote,
    ResourceRecipient, ResourceRecipientCollection)
from onegov.org.models.resource import FindYourSpotCollection
from onegov.org.models.ticket import ticket_submitter, ReservationHandler
from onegov.org.pdf.ticket import TicketPdf
from onegov.org.utils import get_current_tickets_url
from onegov.org.views.message import view_messages_feed
from onegov.org.views.utils import assert_citizen_logged_in
from onegov.org.views.utils import show_tags, show_filters
from onegov.ticket import handlers as ticket_handlers
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.ticket.errors import InvalidStateChange
from onegov.gever.gever_client import GeverClientCAS
from onegov.user import User, UserCollection
from operator import itemgetter
from sqlalchemy import select
from webob import exc
from urllib.parse import urlsplit


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Iterable, Iterator, Mapping
    from email.headerregistry import Address
    from onegov.core.request import CoreRequest
    from onegov.core.types import EmailJsonDict, RenderData, SequenceOrScalar
    from onegov.form.fields import UploadFileWithORMSupport
    from onegov.org.layout import Layout
    from onegov.org.request import OrgRequest
    from onegov.pay import Payment
    from onegov.ticket import TicketInvoiceItem
    from sqlalchemy.orm import Query, Session
    from webob import Response as BaseResponse


@OrgApp.html(model=Ticket, template='ticket.pt', permission=Personal)
def view_ticket(
    self: Ticket,
    request: OrgRequest,
    layout: TicketLayout | None = None
) -> RenderData:

    handler = self.handler

    if handler.deleted:
        # NOTE: We store markup in the snapshot, but since it is JSON
        #       it will be read as a plain string, so we have to wrap
        summary = Markup(self.snapshot.get('summary', ''))  # nosec: B704
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
    is_manager = request.is_manager_for_model(self)
    layout = layout or TicketLayout(self, request)
    payment_button = None
    payment = handler.payment
    edit_amount_url = None

    if is_manager and payment and payment.source == 'manual':
        payment_button = manual_payment_button(payment, layout)
        if not payment.paid:
            edit_amount_url = request.link(self, name='add-invoice-item')

    if is_manager and payment and payment.source in (
        'stripe_connect',
        'datatrans',
        'worldline_saferpay',
    ):
        payment_button = online_payment_button(payment, layout)

    return {
        'title': self.number,
        'layout': layout,
        'ticket': self,
        'summary': summary,
        'deleted': handler.deleted,
        'handler': handler,
        'event_source': handler.data.get('source'),
        'submitter': ticket_submitter(self),
        'submitter_name': handler.submitter_name,
        'submitter_address': handler.submitter_address,
        'submitter_phone': handler.submitter_phone,
        'payment_button': payment_button,
        'counts': counts,
        'feed_data': json.dumps(
            view_messages_feed(messages, request)
        ),
        'edit_amount_url': edit_amount_url,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.form(model=Ticket, permission=Secret, template='form.pt',
             name='delete', form=Form)
def delete_ticket(
    self: Ticket,
    request: OrgRequest,
    form: Form,
    layout: TicketLayout | None = None
) -> RenderData | BaseResponse:
    """ Deleting a ticket means getting rid of all the data associated with it
    """

    layout = layout or TicketLayout(self, request)
    layout.breadcrumbs.append(Link(_('Delete Ticket'), '#'))
    layout.editbar_links = None

    if not self.handler.ticket_deletable:
        return {
            'layout': layout,
            'title': _('Delete Ticket'),
            'callout': _('This ticket is not deletable.'),
            'form': None
        }

    if form.submitted(request):

        delete_messages_from_ticket(request, self.number)

        self.handler.prepare_delete_ticket()

        request.session.delete(self)
        request.success(_('Ticket successfully deleted'))
        return morepath.redirect(get_current_tickets_url(request))

    return {
        'layout': layout,
        'title': _('Delete Ticket'),
        'callout': _(
            'Do you really want to delete this ticket? All data associated '
            'with this ticket will be deleted. This cannot be undone.'
        ),
        'form': form
    }


# FIXME: csrf_token and csrf_protected_url should probably be moved from Layout
#        to CoreRequest making the original methods/attributes on the Layout a
#        pure passthrough, then we can pass the request here
def manual_payment_button(
    payment: Payment,
    layout: Layout,
    css_class: str = 'small secondary'
) -> Link:

    if payment.state == 'open':
        return Link(
            text=_('Mark as paid'),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'mark-as-paid'),
            ),
            attrs={'class': f'mark-as-paid button {css_class}'},
            traits=(
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url,
                ),
            )
        )

    return Link(
        text=_('Mark as unpaid'),
        url=layout.csrf_protected_url(
            layout.request.link(payment, 'mark-as-unpaid'),
        ),
        attrs={'class': f'mark-as-unpaid button {css_class}'},
        traits=(
            Intercooler(
                request_method='POST',
                redirect_after=layout.request.url,
            ),
        )
    )


# FIXME: same here as for manual_payment_button
def online_payment_button(
    payment: Payment,
    layout: Layout,
    css_class: str = 'small secondary'
) -> Link | None:

    if payment.state == 'open':
        return Link(
            text=_('Capture Payment'),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'capture')
            ),
            attrs={'class': f'payment-capture button {css_class}'},
            traits=(
                Confirm(
                    _('Do you really want capture the payment?'),
                    _(
                        'This usually happens automatically, so there is '
                        'no reason not do capture the payment.'
                    ),
                    _('Capture payment'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url
                ),
            )
        )

    if payment.state == 'paid':
        assert payment.amount is not None
        amount = '{:02f} {}'.format(payment.amount, payment.currency)

        return Link(
            text=_('Refund Payment'),
            url=layout.csrf_protected_url(
                layout.request.link(payment, 'refund')
            ),
            attrs={'class': f'payment-refund button {css_class}'},
            traits=(
                Confirm(
                    _('Do you really want to refund ${amount}?', mapping={
                        'amount': amount
                    }),
                    _('This cannot be undone.'),
                    _('Refund ${amount}', mapping={
                        'amount': amount
                    }),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=layout.request.url
                )
            )
        )

    return None


def send_email_if_enabled(
    ticket: Ticket,
    request: OrgRequest,
    template: str,
    subject: str
) -> bool:

    email = ticket.snapshot.get('email') or ticket.handler.email
    if not email:
        return True
    send_ticket_mail(
        request=request,
        template=template,
        subject=subject,
        receivers=(email, ),
        ticket=ticket
    )
    return False


def last_internal_message(
    session: Session,
    ticket_number: str
) -> Message | None:

    messages = MessageCollection[Message](
        session,
        type='ticket_chat',
        channel_id=ticket_number,
        load='newer-first'
    )

    return (
        messages.query()
        .filter(TicketChatMessage.meta['origin'].astext == 'internal')
        .first()
    )


def send_chat_message_email_if_enabled(
    ticket: Ticket,
    request: OrgRequest,
    message: TicketChatMessage,
    origin: str,
    bcc: SequenceOrScalar[Address | str] = (),
    attachments: Iterable[Attachment | StrPath] = ()
) -> None:

    assert origin in ('internal', 'external')
    messages = MessageCollection[TicketChatMessage](
        request.session,
        channel_id=ticket.number,
        type='ticket_chat')

    receiver: str | None
    if origin != 'external':

        # if the messages is sent to the outside, we always send an e-mail
        receiver = ticket.snapshot.get('email') or ticket.handler.email
        reply_to = request.current_username

    else:
        # if the message is sent to the inside, we check the setting on the
        # last message sent to the outside in this ticket - if none exists,
        # we do not notify
        last_internal = last_internal_message(request.session, ticket.number)

        receiver = None
        always_notify = request.app.org.ticket_always_notify

        if last_internal:
            if last_internal.meta.get('notify') or always_notify:
                receiver = last_internal.owner
        elif always_notify and ticket.user:
            receiver = ticket.user.username

        reply_to = None  # default reply-to given by the application

    if not receiver:
        return

    # we show the previous messages by going back until we find a message
    # that is not from the same author as the new message (this should usually
    # be the next message, but might include multiple, if someone sent a bunch
    # of messages in succession without getting a reply)
    #
    # note that the resulting thread has to be reversed for the mail template
    def thread() -> Iterator[TicketChatMessage]:
        messages.older_than = message.id
        messages.load = 'newer-first'

        for m in messages.query():
            yield m

            if m.owner != message.owner:
                break

    send_ticket_mail(
        request=request,
        template='mail_ticket_chat_message.pt',
        subject=_('Your ticket has a new message'),
        content={
            'model': ticket,
            'message': message,
            'thread': tuple(reversed(list(thread()))),
        },
        ticket=ticket,
        receivers=(receiver,),
        reply_to=reply_to,
        force=True,
        bcc=bcc,
        attachments=attachments
    )


def send_new_note_notification(
    request: OrgRequest,
    form: TicketNoteForm,
    note: TicketNote,
    template: str
) -> None:
    """
    Sends an E-mail notification to all resource recipients that have been
    configured to receive notifications for new (ticket) notes.
    """

    ticket = note.ticket
    assert ticket is not None
    handler = ticket.handler

    if not isinstance(handler, ReservationHandler) or not handler.resource:
        return

    def recipients_which_have_registered_for_mail() -> Iterator[str]:
        q = ResourceRecipientCollection(request.session).query()
        q = q.filter(ResourceRecipient.medium == 'email')
        q = q.order_by(None).order_by(ResourceRecipient.address)
        q = q.with_entities(ResourceRecipient.address,
                            ResourceRecipient.content)
        for r in q:
            if handler.reservations[0].resource.hex in r.content[
                'resources'
            ] and r.content.get('internal_notes', False):
                yield r.address

    title = request.translate(
        _(
            '${org} New Note in Reservation for ${resource_title}',
            mapping={
                'org': request.app.org.title,
                'resource_title': handler.resource.title,
            },
        )
    )
    assert hasattr(ticket, 'reference')
    content = render_template(
        template,
        request,
        {
            'layout': DefaultMailLayout(object(), request),
            'title': title,
            'form': form,
            'model': ticket,
            'resource': handler.resource,
            'show_submission': True,
            'reservations': handler.reservations,
            'message': note,
            'ticket_reference': ticket.reference(request),
        },
    )
    plaintext = html_to_text(content)

    def email_iter() -> Iterator[EmailJsonDict]:
        for recipient_addr in recipients_which_have_registered_for_mail():

            yield request.app.prepare_email(
                receivers=(recipient_addr,),
                subject=title,
                content=content,
                plaintext=plaintext,
                category='transactional',
                attachments=(),
            )

    request.app.send_transactional_email_batch(email_iter())


@OrgApp.form(
    model=Ticket, name='note', permission=Personal,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def handle_new_note(
    self: Ticket,
    request: OrgRequest,
    form: TicketNoteForm,
    layout: TicketNoteLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        message = form.text.data
        assert message is not None
        note = TicketNote.create(self, request, message, form.file.create())
        request.success(_('Your note was added'))

        if note.text and note.text[0]:
            send_new_note_notification(
                request,
                form,
                note,
                'mail_internal_notes_notification.pt',
            )

        return request.redirect(request.link(self))

    return {
        'title': _('New Note'),
        'layout': layout or TicketNoteLayout(self, request, _('New Note')),
        'form': form,
        'hint': 'default'
    }


@OrgApp.view(model=TicketNote, permission=Personal)
def view_ticket_note(
    self: TicketNote,
    request: OrgRequest
) -> BaseResponse:
    return request.redirect(request.link(self.ticket))


def assert_can_modify_note(self: TicketNote, request: OrgRequest) -> None:
    if not (
        self.owner == request.current_username
        or request.is_manager_for_model(self)
    ):
        raise exc.HTTPNotFound()


@OrgApp.view(model=TicketNote, permission=Personal, request_method='DELETE')
def delete_ticket_note(self: TicketNote, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    assert_can_modify_note(self, request)

    if self.ticket:
        # force a change of the ticket to make sure that it gets reindexed
        self.ticket.force_update()

    request.session.delete(self)
    request.success(_('The note was deleted'))


@OrgApp.form(
    model=TicketNote, name='edit', permission=Personal,
    template='ticket_note_form.pt', form=TicketNoteForm
)
def handle_edit_note(
    self: TicketNote,
    request: OrgRequest,
    form: TicketNoteForm,
    layout: TicketNoteLayout | None = None
) -> RenderData | BaseResponse:

    assert_can_modify_note(self, request)

    assert self.ticket is not None
    if form.submitted(request):
        form.populate_obj(self)
        self.owner = request.current_username

        # force a change of the ticket to make sure that it gets reindexed
        self.ticket.force_update()

        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.ticket))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or TicketNoteLayout(self.ticket, request, _('New Note'))
    return {
        'title': _('Edit Note'),
        'layout': layout,
        'form': form,
        'hint': self.owner != request.current_username and 'owner'
    }


@OrgApp.view(model=Ticket, name='accept', permission=Private)
def accept_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:
    user = request.current_user
    assert user is not None

    was_pending = self.state == 'open'

    try:
        self.accept_ticket(user)
    except InvalidStateChange:
        request.alert(_("The ticket cannot be accepted because it's not open"))
    else:
        if was_pending:
            TicketMessage.create(self, request, 'accepted')
            request.success(_('You have accepted ticket ${number}', mapping={
                'number': self.number
            }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='close', permission=Private)
def close_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:

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
            request.success(_('You have closed ticket ${number}', mapping={
                'number': self.number
            }))

            email_missing = send_email_if_enabled(
                ticket=self,
                request=request,
                template='mail_ticket_closed.pt',
                subject=_('Your request has been closed.')
            )
            if email_missing:
                request.alert(_('The submitter email is not available'))

    return morepath.redirect(get_current_tickets_url(request))


@OrgApp.view(model=Ticket, name='reopen', permission=Private)
def reopen_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:
    user = request.current_user
    assert user is not None

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
            request.success(_('You have reopened ticket ${number}', mapping={
                'number': self.number
            }))

            if request.email_for_new_tickets:
                send_ticket_mail(
                    request=request,
                    template='mail_ticket_opened_info.pt',
                    subject=_('New ticket'),
                    ticket=self,
                    receivers=(request.email_for_new_tickets, ),
                    content={
                        'model': self
                    }
                )

            email_missing = send_email_if_enabled(
                ticket=self,
                request=request,
                template='mail_ticket_reopened.pt',
                subject=_('Your ticket has been reopened')
            )
            if email_missing:
                request.alert(_('The submitter email is not available'))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='mute', permission=Private)
def mute_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:
    self.muted = True

    TicketMessage.create(self, request, 'muted')
    request.success(
        _('You have disabled e-mails for ticket ${number}', mapping={
            'number': self.number
        }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='unmute', permission=Private)
def unmute_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:
    self.muted = False

    TicketMessage.create(self, request, 'unmuted')
    request.success(
        _('You have enabled e-mails for ticket ${number}', mapping={
            'number': self.number
        }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='archive', permission=Private)
def archive_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:

    try:
        self.archive_ticket()
    except InvalidStateChange:
        request.alert(
            _("The ticket cannot be archived because it's not closed"))
    else:
        TicketMessage.create(self, request, 'archived')
        request.success(_('You archived ticket ${number}', mapping={
            'number': self.number
        }))

    return morepath.redirect(request.link(self))


@OrgApp.view(model=Ticket, name='unarchive', permission=Private)
def unarchive_ticket(self: Ticket, request: OrgRequest) -> BaseResponse:
    user = request.current_user
    assert user is not None

    try:
        self.unarchive_ticket(user)
    except InvalidStateChange:
        request.alert(
            _(
                "The ticket cannot be recovered from the archive because it's "
                "not archived"
            ))
    else:
        TicketMessage.create(self, request, 'unarchived')
        request.success(
            _('You recovered ticket ${number} from the archive', mapping={
              'number': self.number
              }))

    return morepath.redirect(request.link(self))


@OrgApp.form(model=Ticket, name='assign', permission=Private,
             form=TicketAssignmentForm, template='form.pt')
def assign_ticket(
    self: Ticket,
    request: OrgRequest,
    form: TicketAssignmentForm,
    layout: TicketLayout | None = None
) -> RenderData | BaseResponse:

    if form.submitted(request):
        assert form.username is not None
        TicketMessage.create(
            self, request, 'assigned',
            old_owner=self.user.username if self.user else '',
            new_owner=form.username
        )
        send_ticket_mail(
            request=request,
            template='mail_ticket_assigned.pt',
            subject=_('You have a new ticket'),
            receivers=(form.username, ),
            ticket=self,
            force=True
        )
        self.user_id = form.user.data
        request.success(_('Ticket assigned'))
        return morepath.redirect(request.link(self))

    return {
        'title': _('Assign ticket'),
        'layout': layout or TicketLayout(self, request),
        'form': form,
    }


@OrgApp.form(model=Ticket, name='change-tag', permission=Private,
             form=TicketChangeTagForm, template='form.pt')
def change_tag(
    self: Ticket,
    request: OrgRequest,
    form: TicketChangeTagForm,
    layout: TicketLayout | None = None
) -> RenderData | BaseResponse:

    if self.state != 'pending' or not request.app.org.ticket_tags:
        raise exc.HTTPNotFound()

    if form.submitted(request):
        self.tag = form.tag.data
        selected_meta = {}
        for item in request.app.org.ticket_tags:
            if not isinstance(item, dict):
                continue

            tag, meta = next(iter(item.items()))
            if tag == form.tag.data:
                selected_meta = meta
                break

        # NOTE: Don't include the E-Mail in the selected meta
        selected_meta.pop('E-Mail', None)

        # NOTE: We don't modify the submission data but we exclude
        #       any metadata that's tied to the submission
        if selected_meta and (
            submission := getattr(self.handler, 'submission', None)
        ):
            form = submission.form_class()
            selected_meta = {
                key: value
                for key, value in selected_meta.items()
                if not any(
                    True
                    for field in form
                    if field.label.text == key
                )
            }

        # update the key code if it's different
        kaba_code = selected_meta.pop('Kaba Code', None)
        handler_data = self.handler_data or {}
        if kaba_code and handler_data.get('key_code') != kaba_code:
            handler_data['key_code'] = kaba_code
            self.handler_data = handler_data

        self.tag_meta = selected_meta

        request.success(_('Tag changed'))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.tag.data = self.tag

    return {
        'title': _('Change tag'),
        'layout': layout or TicketLayout(self, request),
        'form': form,
    }


@OrgApp.form(model=Ticket, name='message-to-submitter', permission=Private,
             form=ExtendedInternalTicketChatMessageForm, template='form.pt')
def message_to_submitter(
    self: Ticket,
    request: OrgRequest,
    form: ExtendedInternalTicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | BaseResponse:

    recipient = self.snapshot.get('email') or self.handler.email

    if not recipient:
        request.alert(_('The submitter email is not available'))
        return request.redirect(request.link(self))

    if form.submitted(request):
        assert form.text.data is not None
        assert request.current_username is not None
        if self.state == 'closed':
            request.alert(_('The ticket has already been closed'))
        else:
            message = TicketChatMessage.create(
                self, request,
                text=form.text.data,
                owner=request.current_username,
                recipient=recipient,
                notify=form.notify.data,
                origin='internal')

            fe = form.email_attachment
            send_chat_message_email_if_enabled(
                self,
                request,
                message,
                origin='internal',
                bcc=form.email_bcc.data or (),
                attachments=create_attachment_from_uploaded(fe, request)
            )

            request.success(_('Your message has been sent'))
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
        'title': _('New Message'),
        'layout': layout or TicketChatMessageLayout(self, request),
        'form': form,
        'helptext': _(
            'The following message will be sent to ${address} and it will be '
            'recorded for future reference.', mapping={
                'address': recipient
            }
        )
    }


def create_attachment_from_uploaded(
    fe: UploadFileWithORMSupport,
    request: OrgRequest
) -> tuple[Attachment, ...]:

    filename, storage_path = (
        fe.data.get('filename') if fe.data else None,
        request.app.depot_storage_path,
    )

    if not (filename and storage_path):
        return ()

    file = fe.create()
    if not file:
        return ()

    file_path = os.path.join(storage_path, file.reference['path'])
    attachment = Attachment(
        file_path, file.reference.file.read(), file.reference['content_type']
    )
    attachment.filename = filename
    return (attachment,)


@OrgApp.view(model=Ticket, name='pdf', permission=Personal)
def view_ticket_pdf(self: Ticket, request: OrgRequest) -> Response:
    """ View the generated PDF. """

    content = TicketPdf.from_ticket(request, self)

    return Response(
        content.read(),
        content_type='application/pdf',
        content_disposition='inline; filename={}_{}.pdf'.format(
            normalize_for_url(self.number),
            date.today().strftime('%Y%m%d')
        )
    )


@OrgApp.view(model=Ticket, name='files', permission=Private)
def view_ticket_files(self: Ticket, request: OrgRequest) -> BaseResponse:
    """ Download the files associated with the ticket as zip. """

    form_submission = getattr(self.handler, 'submission', None)

    if form_submission is None:
        return request.redirect(request.link(self))

    buffer = BytesIO()
    not_existing = []
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in form_submission.files:
            try:
                zipf.writestr(f.name, f.reference.file.read())
            except OSError:
                not_existing.append(f.name)

        pdf = TicketPdf.from_ticket(request, self)
        pdf_filename = '{}_{}.pdf'.format(normalize_for_url(self.number),
                                          date.today().strftime('%Y%m%d'))
        zipf.writestr(pdf_filename, pdf.read())

    if not_existing:
        count = len(not_existing)
        request.alert(_(f"{count} file(s) not found:"
                        f" {', '.join(not_existing)}"))
    else:
        request.info(_('Zip archive created successfully'))

    buffer.seek(0)

    return Response(
        buffer.read(),
        content_type='application/zip',
        content_disposition='inline; filename=ticket-{}_{}.zip'.format(
            normalize_for_url(self.number),
            date.today().strftime('%Y%m%d')
        )
    )


@OrgApp.html(
    model=Ticket,
    name='invoice',
    template='ticket_invoice.pt',
    permission=Private
)
def view_ticket_invoice(
    self: Ticket,
    request: OrgRequest,
    layout: TicketInvoiceLayout | None = None
) -> RenderData:

    invoice = self.invoice
    if invoice is None:
        raise exc.HTTPNotFound()

    payment = self.payment
    if payment is not None and (
        payment.source != 'manual'
        or payment.state != 'open'
    ):
        request.warning(_(
            'The payment is no longer open, so the invoice '
            'cannot be modified.'
        ))

    payment = self.payment

    def item_actions(item: TicketInvoiceItem) -> list[Link]:
        if item.group != 'manual':
            return []

        if payment is not None and (
            payment.source != 'manual'
            or payment.state != 'open'
        ):
            return []

        return [Link(
            '',
            attrs={
                'class': 'fa fa-trash remove-invoice-item',
                'title': _('Remove')
            },
            url=request.csrf_protected_url(request.link(
                self,
                'remove-invoice-item',
                query_params={'item': item.id.hex}
            )),
            traits=(
                Confirm(
                    _('Remove Discount') if item.amount < 0 else
                    _('Remove Surchage'),
                    _(
                        'Do you really want to remove "${booking_text}"?',
                        mapping={'booking_text': item.text}
                    )
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=request.url
                ),
            )
        )]

    layout = layout or TicketInvoiceLayout(self, request)

    def sort_key(item: TicketInvoiceItem) -> tuple[int, str]:
        match item.group:
            case 'submission' | 'reservation' | 'migration':
                return 0, item.group
            case 'form':
                return 1, item.group
            case 'manual' | 'reduced_amount':
                return 99, 'manual'
            case _:
                return 2, item.group

    invoice_items = {
        group: list(items)
        for (__, group), items in groupby(
            sorted(invoice.items, key=sort_key),
            key=sort_key
        )
    }

    payment_button: Link | None = None
    if payment and payment.source == 'manual':
        payment_button = manual_payment_button(
            payment, layout, css_class='primary')

    if payment and payment.source in (
        'stripe_connect',
        'datatrans',
        'worldline_saferpay',
    ):
        payment_button = online_payment_button(
            payment, layout, css_class='primary')

    return {
        'title': _('${ticket} Invoice', mapping={'ticket': self.number}),
        'layout': layout,
        'ticket': self,
        'invoice': invoice,
        'invoice_items': invoice_items,
        'payment': payment,
        'payment_button': payment_button,
        'item_actions': item_actions
    }


@OrgApp.form(
    model=Ticket,
    name='add-invoice-item',
    template='form.pt',
    permission=Private,
    form=ManualInvoiceItemForm
)
def add_invoice_item(
    self: Ticket,
    request: OrgRequest,
    form: ManualInvoiceItemForm,
    layout: TicketInvoiceLayout | None = None
) -> RenderData | BaseResponse:

    invoice = self.invoice
    if invoice is None:
        raise exc.HTTPNotFound()

    payment = self.payment
    if payment is not None and (
        payment.source != 'manual'
        or payment.state != 'open'
    ):
        return morepath.redirect(request.link(self, 'invoice'))

    if form.submitted(request):
        assert form.booking_text.data is not None
        item = invoice.add(
            text=form.booking_text.data,
            group='manual',
            family=form.kind.data,
            unit=form.amount,
        )
        if payment is not None:
            item.payments.append(payment)
            item.paid = payment.state == 'paid'
        request.session.flush()
        self.handler.refresh_invoice_items(request)
        return morepath.redirect(request.link(self, 'invoice'))

    layout = layout or TicketInvoiceLayout(self, request)

    return {
        'title': _('Add Discount / Surcharge'),
        'layout': layout,
        'form': form,
    }


@OrgApp.view(
    model=Ticket,
    name='remove-invoice-item',
    permission=Private,
    request_method='DELETE'
)
def remove_invoice_item(
    self: Ticket,
    request: OrgRequest,
    layout: TicketInvoiceLayout | None = None
) -> None:

    request.assert_valid_csrf_token()

    invoice = self.invoice
    if invoice is None:
        raise exc.HTTPNotFound()

    payment = self.payment
    if payment is not None and (
        payment.source != 'manual'
        or payment.state != 'open'
    ):
        request.alert(_(
            'The payment is no longer open, so the invoice '
            'cannot be modified.'
        ))
        return

    target: TicketInvoiceItem | None = None
    item_id = request.GET.get('item')
    for item in invoice.items:
        if item.id.hex == item_id:
            target = item
            break

    if target is None or target.group != 'manual':
        raise exc.HTTPNotFound()

    target.payments = []
    invoice.items.remove(target)
    request.session.delete(target)
    request.session.flush()
    self.handler.refresh_invoice_items(request)


@OrgApp.form(model=Ticket, name='status', template='ticket_status.pt',
             permission=Public, form=TicketChatMessageForm)
def view_ticket_status(
    self: Ticket,
    request: OrgRequest,
    form: TicketChatMessageForm,
    layout: TicketChatMessageLayout | None = None
) -> RenderData | BaseResponse:

    title = ''
    if self.state == 'open':
        title = _('Your request has been submitted')
    elif self.state == 'pending':
        title = _('Your request is currently pending')
    elif self.state == 'closed' or self.state == 'archived':
        title = _('Your request has been processed')

    if request.is_logged_in:
        status_text = _('Ticket Status')
        closed_text = _('The ticket has already been closed')
    else:
        # We adjust the wording for users that do not know what a ticket is
        status_text = _('Request Status')
        closed_text = _('The request has already been closed')

    layout = layout or TicketChatMessageLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(status_text, '#')
    ]

    if form.submitted(request):
        assert form.text.data is not None

        if self.state == 'closed':
            request.alert(closed_text)
        else:
            # Note that this assumes email BCC recipients are internal
            # recipients and have `current_username` in all cases. If we allow
            # external BCC recipients, we'll have to change this
            if request.current_username != self.handler.email:
                owner = request.current_username
            else:
                owner = self.handler.email

            message = TicketChatMessage.create(
                self, request,
                text=form.text.data,
                owner=owner or '',
                origin='external')

            send_chat_message_email_if_enabled(
                self, request, message, origin='external')

            request.success(_('Your message has been received'))
            return morepath.redirect(request.link(self, 'status'))

    messages = MessageCollection(
        request.session,
        channel_id=self.number,
        type=request.app.settings.org.public_ticket_messages
    )

    pick_up_hint = None
    if resource := getattr(self.handler, 'resource', None):
        pick_up_hint = resource.pick_up
    if submission := getattr(self.handler, 'submission', None):
        if form_definition := getattr(submission, 'form', None):
            pick_up_hint = form_definition.pick_up

    return {
        'title': title,
        'layout': layout,
        'ticket': self,
        'feed_data': messages and json.dumps(
            view_messages_feed(messages, request)
        ) or None,
        'form': form,
        'pick_up_hint': pick_up_hint
    }


@OrgApp.view(model=Ticket, name='send-to-gever', permission=Private)
def view_send_to_gever(self: Ticket, request: OrgRequest) -> BaseResponse:
    org = request.app.org
    username = org.gever_username
    password = org.gever_password
    endpoint = org.gever_endpoint

    if not (username and password and endpoint):
        request.alert(_('Could not find valid credentials. You can set them '
                        'in Gever API Settings.'))
        return morepath.redirect(request.link(self))

    password_dec = request.app.decrypt(password.encode('utf-8'))

    pdf = TicketPdf.from_ticket(request, self)
    filename = '{}_{}.pdf'.format(
        normalize_for_url(self.number),
        date.today().strftime('%Y%m%d')
    )

    base_url = '{0.scheme}://{0.netloc}/'.format(urlsplit(endpoint))
    client = GeverClientCAS(username, password_dec, service_url=base_url)
    try:
        resp = client.upload_file(pdf.read(), filename, endpoint)
    except (KeyError, ValueError):
        msg = _('Encountered an error while uploading to Gever.')
        request.alert(msg)
        return morepath.redirect(request.link(self))

    # server will respond with status 204 after a successful upload.
    if not (resp.status_code == 204 and 'Location' in resp.headers.keys()):
        msg = _('Encountered an error while uploading to Gever. Response '
                'status code is ${status}.', mapping={
                    'status': resp.status_code})
        request.alert(msg)
        return morepath.redirect(request.link(self))

    TicketMessage.create(
        self,
        request,
        'uploaded'
    )
    request.success(_('Successfully uploaded the PDF of this ticket to Gever'))
    return morepath.redirect(request.link(self))


def get_filters(
    self: TicketCollection,
    request: OrgRequest
) -> Iterator[Link]:

    assert request.current_user is not None
    yield Link(
        text=_('My'),
        url=request.link(
            self.for_state('unfinished').for_owner(request.current_user.id)
        ),
        active=self.state == 'unfinished',
        attrs={'class': 'ticket-filter-my'}
    )
    for id, text in TICKET_STATES.items():
        if id != 'archived':
            yield Link(
                text=text,
                url=request.link(
                    self.for_state(id)
                    # FIXME: This is another case where we pass invalid
                    #        state just so the generated URL is shorter
                    #        we should make morepath aware of defaults
                    #        so it can ellide parameters that have been
                    #        set to their default value automatically
                    .for_owner(None)  # type:ignore[arg-type]
                ),
                active=self.state == id,
                attrs={'class': 'ticket-filter-' + id}
            )


def get_groups(
    self: TicketCollection | ArchivedTicketCollection,
    request: OrgRequest,
    groups: Mapping[str, Iterable[str]],
    handler: str
) -> Iterator[Link]:

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


def get_handlers(
    self: TicketCollection | ArchivedTicketCollection,
    request: OrgRequest,
    groups: Mapping[str, Iterable[str]]
) -> Iterator[Link]:

    handlers = []

    for key, handler in ticket_handlers.registry.items():
        if key in groups:
            assert hasattr(handler, 'handler_title')
            handlers.append(
                (key, request.translate(handler.handler_title)))

    handlers.sort(key=itemgetter(1))
    handlers.insert(0, ('ALL', _('All Tickets')))

    for id, text in handlers:
        grouplinks = (
            tuple(get_groups(self, request, groups, id))
            if id != 'ALL' else ()
        )
        css_class = id + '-link is-parent' if grouplinks else id + '-link'

        yield Link(
            text=text,
            url=request.link(
                self.for_handler(id)
                # FIXME: This is another case where we pass invalid
                #        state just so the generated URL is shorter
                #        we should make morepath aware of defaults
                #        so it can ellide parameters that have been
                #        set to their default value automatically
                .for_group(None)  # type:ignore[arg-type]
            ),
            active=self.handler == id and self.group is None,
            attrs={'class': css_class}
        )

        yield from grouplinks


def get_owners(
    self: TicketCollection | ArchivedTicketCollection,
    request: OrgRequest
) -> Iterator[Link]:

    users = UserCollection(request.session)
    query = users.by_roles(*request.app.settings.org.ticket_manager_roles)
    query = query.order_by(User.title)

    yield Link(
        text=_('All Users'),
        url=request.link(self.for_owner('*')),
        active=self.owner == '*'
    )

    for user in query:
        yield Link(
            text=user.title,
            url=request.link(self.for_owner(user.id)),
            active=self.owner == user.id.hex,
            model=user
        )


def groups_by_handler_code(session: Session) -> dict[str, list[str]]:
    query = as_selectable("""
            SELECT
                handler_code,                         -- Text
                ARRAY_AGG(DISTINCT "group") AS groups -- ARRAY(Text)
            FROM tickets GROUP BY handler_code
        """)

    groups = {
        r.handler_code: r.groups
        for r in session.execute(select(query.c))
    }
    for handler in groups:
        groups[handler].sort(key=lambda g: normalize_for_url(g))

    return groups


@OrgApp.html(
    model=TicketCollection,
    template='tickets.pt',
    permission=Private
)
def view_tickets(
    self: TicketCollection,
    request: OrgRequest,
    layout: TicketsLayout | None = None
) -> RenderData:

    # remember where we last were in the tickets view
    request.browser_session.tickets_state = {
        'handler': self.handler,
        'group': self.group,
        'state': self.state,
        'owner': self.owner,
        'page': self.page,
        'extra_parameters': self.extra_parameters,
    }

    groups = groups_by_handler_code(request.session)
    handlers = tuple(get_handlers(self, request, groups))
    owners = tuple(get_owners(self, request))
    filters = tuple(get_filters(self, request))
    handler = next((h for h in handlers if h.active), None)
    owner = next((o for o in owners if o.active), None)
    layout = layout or TicketsLayout(self, request)

    def archive_link(ticket: Ticket) -> str:
        return layout.csrf_protected_url(request.link(ticket, name='archive'))

    return {
        'title': _('Tickets'),
        'layout': layout,
        'tickets': self.batch,
        'filters': filters,
        'handlers': handlers,
        'owners': owners,
        'tickets_state': self.state,
        'archive_tickets': self.state == 'closed',
        'has_handler_filter': self.handler != 'ALL',
        'has_owner_filter': self.owner != '*',
        'handler': handler,
        'owner': owner,
        'action_link': archive_link
    }


@OrgApp.html(
    model=ArchivedTicketCollection,
    template='archived_tickets.pt',
    permission=Private
)
def view_archived_tickets(
    self: ArchivedTicketCollection,
    request: OrgRequest,
    layout: ArchivedTicketsLayout | None = None
) -> RenderData:

    groups = groups_by_handler_code(request.session)
    handlers = tuple(get_handlers(self, request, groups))
    owners = tuple(get_owners(self, request))
    handler = next((h for h in handlers if h.active), None)
    owner = next((o for o in owners if o.active), None)
    layout = layout or ArchivedTicketsLayout(self, request)

    def action_link(ticket: Ticket) -> str:
        return ''

    return {
        'title': _('Archived Tickets'),
        'layout': layout,
        'tickets': self.batch,
        'filters': [],
        'handlers': handlers,
        'owners': owners,
        'tickets_state': self.state,
        'archive_tickets': False,
        'has_handler_filter': self.handler != 'ALL',
        'has_owner_filter': self.owner != '*',
        'handler': handler,
        'owner': owner,
        'action_link': action_link
    }


@OrgApp.html(
    model=ArchivedTicketCollection,
    name='delete',
    request_method='DELETE',
    permission=Secret
)
def view_delete_all_archived_tickets(
    self: ArchivedTicketCollection,
    request: OrgRequest
) -> None:

    tickets = self.query().filter_by(state='archived')

    errors, ok = delete_tickets_and_related_data(request, tickets)
    if errors:
        msg = request.translate(_(
            '${success_count} tickets deleted, '
            '${error_count} are not deletable',
            mapping={'success_count': len(ok), 'error_count': len(errors)},
        ))
        request.message(msg, 'warning')
    else:
        msg = request.translate(_(
            '${success_count} tickets deleted.',
            mapping={'success_count': len(ok)}
        ))
        request.message(msg, 'success')


def delete_tickets_and_related_data(
    request: CoreRequest, tickets: Query[Ticket]
) -> tuple[list[Ticket], list[Ticket]]:

    not_deletable, successfully_deleted = [], []

    for ticket in tickets:
        if not ticket.handler.ticket_deletable:
            not_deletable.append(ticket)

            ticket.redact_data()
            continue

        ticket.handler.prepare_delete_ticket()
        delete_messages_from_ticket(request, ticket.number)

        if submission := getattr(ticket.handler, 'submission', None):
            # cascade delete should take care of the ticket's files
            request.session.delete(submission)

        request.session.delete(ticket)
        successfully_deleted.append(ticket)

    return not_deletable, successfully_deleted


def delete_messages_from_ticket(request: CoreRequest, number: str) -> None:
    messages = MessageCollection(
        request.session, channel_id=number
    )
    for message in messages.query():
        messages.delete(message)


@OrgApp.html(model=FindYourSpotCollection, name='tickets',
             template='pending_tickets.pt', permission=Public)
def view_pending_tickets(
    self: FindYourSpotCollection,
    request: OrgRequest,
    layout: FindYourSpotLayout | None = None
) -> RenderData:

    pending: dict[str, list[str]]
    pending = request.browser_session.get('reservation_tickets', {})
    ticket_ids = pending.get(self.group or '', [])
    if not ticket_ids:
        raise exc.HTTPForbidden()

    query = request.session.query(Ticket)
    query = query.filter(Ticket.id.in_(ticket_ids))
    tickets = query.all()

    return {
        'title': _('Submitted Requests'),
        'layout': layout or FindYourSpotLayout(self, request),
        'tickets': tickets,
    }


@OrgApp.html(
    model=TicketCollection,
    name='my-tickets',
    template='pending_tickets.pt',
    permission=Public
)
def view_my_tickets(
    self: TicketCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    assert_citizen_logged_in(request)
    assert request.authenticated_email

    tickets = (
        self.by_ticket_email(request.authenticated_email)
        .order_by(Ticket.created.desc())
        .all()
    )

    layout = layout or DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Dashboard'), request.class_link(CitizenDashboard)),
        Link(_('Submitted Requests'), '#')
    ]

    return {
        'title': _('Submitted Requests'),
        'layout': layout,
        'tickets': tickets,
    }
