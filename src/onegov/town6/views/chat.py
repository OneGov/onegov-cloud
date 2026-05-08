from __future__ import annotations

from onegov.core.security import Private, Public
from onegov.town6 import TownApp
from morepath import redirect

from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.core.templates import render_template
from onegov.org.layout import DefaultMailLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage
from onegov.org.utils import emails_for_new_ticket
from onegov.ticket import TicketCollection
from onegov.town6 import _
from onegov.town6.forms.chat import ChatInitiationForm, ChatActionsForm
from onegov.town6.layout import StaffChatLayout, ClientChatLayout
from onegov.town6.layout import DefaultLayout, ArchivedChatsLayout
from onegov.user import User
from webob.exc import HTTPForbidden


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=ChatCollection,
    template='chats_staff.pt',
    form=ChatActionsForm,
    permission=Private)
def view_chats_staff(
    self: ChatCollection,
    request: TownRequest,
    form: ChatActionsForm
) -> RenderData:

    user = request.current_user
    assert user is not None

    all_chats = ChatCollection(request.session).query()
    open_requests = all_chats.filter(Chat.user_id == None).filter(
        Chat.chat_history != []
    ).filter(Chat.active == True)
    active_chats = all_chats.filter(Chat.user_id == user.id).filter(
        Chat.active == True)

    if form.submitted(request):
        chat = ChatCollection(request.session).query().filter(
            Chat.id == form.chat_id.data).one()

        action = request.POST.get('chat-action')
        if action == 'end-chat':
            args: RenderData = {
                'layout': DefaultMailLayout(object(), request),
                'title': request.translate(
                    _('Chat History with ${org}', mapping={
                        'org': request.app.org.title
                    })
                ),
                'organisation': request.app.org.title,
                'chat': chat,
            }

            request.app.send_transactional_email(
                subject=args['title'],
                receivers=(chat.email, user.username),
                content=render_template(
                    'mail_chat_customer.pt', request, args
                )
            )

        elif action == 'create-ticket':
            with all_chats.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code='CHT', handler_id=chat.id.hex
                )
                TicketMessage.create(ticket, request, 'opened', 'external')

                send_ticket_mail(
                    request=request,
                    template='mail_turned_chat_into_ticket.pt',
                    subject=_('Your Chat has been turned into a ticket'),
                    receivers=(chat.email, ),
                    ticket=ticket,
                    content={
                        'model': self,
                        'ticket': ticket,
                        'chat': chat,
                        'organisation': request.app.org.title,
                    }
                )
                for email in emails_for_new_ticket(request, ticket):
                    send_ticket_mail(
                        request=request,
                        template='mail_ticket_opened_info.pt',
                        subject=_('New ticket'),
                        ticket=ticket,
                        receivers=(email, ),
                        content={'model': ticket},
                    )

                request.app.send_websocket(
                    channel=request.app.websockets_private_channel,
                    message={
                        'event': 'browser-notification',
                        'title': request.translate(_('New ticket')),
                        'created': ticket.created.isoformat()
                    },
                    groupids=request.app.groupids_for_ticket(ticket),
                )

    return {
        'title': _('Chats'),
        'form': form,
        'layout': StaffChatLayout(self, request),
        'user': user,
        'open_requests': open_requests.all(),
        'active_chats': active_chats.all()
    }


@TownApp.html(
    model=ChatCollection,
    template='chats_archive.pt',
    name='archive',
    permission=Private)
def view_chats_archive(
    self: ChatCollection,
    request: TownRequest
) -> RenderData:

    user = request.current_user

    return {
        'title': _('Archived Chats'),
        'layout': ArchivedChatsLayout(self, request),
        'user': user,
        'archived_chats': self.batch
    }


@TownApp.form(
    model=ChatCollection,
    template='form.pt',
    name='initiate',
    permission=Public,
    form=ChatInitiationForm)
def view_chat_form(
    self: ChatCollection,
    request: TownRequest,
    form: ChatInitiationForm
) -> RenderData | Response:

    if not request.app.chat_open(request) and not request.is_manager:
        raise HTTPForbidden()

    active_chat_id = request.browser_session.get('active_chat_id')
    if active_chat_id and (chat := self.by_id(active_chat_id)) and chat.active:
        return redirect(request.link(chat))

    if form.submitted(request):
        assert form.name.data is not None
        assert form.email.data is not None
        chat = self.add(
            form.name.data,
            form.email.data,
            form.topic.data if form.topic else _('General')
        )
        request.browser_session['active_chat_id'] = chat.id
        return redirect(request.link(chat))

    return {
        'title': _('Chat Customer'),
        'layout': DefaultLayout(self, request),
        'form': form
    }


@TownApp.html(
    model=Chat,
    template='chat_customer.pt',
    permission=Public)
def view_customer_chat(self: Chat, request: TownRequest) -> RenderData:

    active_chat_id = request.browser_session.get('active_chat_id')
    if not request.is_manager and self.id != active_chat_id:
        raise HTTPForbidden()

    return {
        'title': _('Chat Customer'),
        'layout': ClientChatLayout(self, request),
        'chat': self,
        'customer_name': self.customer_name
    }


@TownApp.html(
    model=Chat,
    template='chat_staff.pt',
    name='staff-view',
    permission=Public)
def view_staff_chat(self: Chat, request: TownRequest) -> RenderData:

    active_chat_id = request.browser_session.get('active_chat_id')
    if not request.is_manager and self.id != active_chat_id:
        raise HTTPForbidden()

    staff = request.session.query(User).filter_by(
        id=self.user_id).first()
    staff_username = staff.username if staff else ''

    return {
        'title': f'Chat {self.customer_name}',
        'layout': ArchivedChatsLayout(self, request),
        'chat': self,
        'customer_name': self.customer_name,
        'staff': staff_username
    }
