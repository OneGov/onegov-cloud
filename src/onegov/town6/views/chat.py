from onegov.core.security import Private, Public
from onegov.town6 import TownApp
from morepath import redirect

from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.town6.forms.chat import ChatInitiationForm, ChatActionsForm
from onegov.core.templates import render_template
from onegov.town6.layout import StaffChatLayout, ClientChatLayout
from onegov.town6.layout import DefaultLayout
from onegov.org.layout import DefaultMailLayout
from onegov.org.mail import send_ticket_mail
from webob.exc import HTTPForbidden
from onegov.town6 import _
from onegov.org.models import TicketMessage
from onegov.ticket import TicketCollection


@TownApp.form(
    model=ChatCollection,
    template='chats_staff.pt',
    form=ChatActionsForm,
    permission=Private)
def view_chats_staff(self, request, form):

    user = request.current_user

    all_chats = ChatCollection(request.session).query()
    open_requests = all_chats.filter(Chat.user_id == None).filter(
        Chat.chat_history != []
    ).filter(Chat.active == True)
    active_chats = all_chats.filter(Chat.user_id == user.id).filter(
        Chat.active == True)
    archived_chats = all_chats.filter(
        Chat.active == False)

    if form.submitted(request):
        chat = ChatCollection(request.session).query().filter(
            Chat.id == form.chat_id.data).one()

        if request.POST._items[2][1] == 'end-chat':
            args = {
                'layout': DefaultMailLayout(object(), request),
                'title': request.translate(
                    _("Chat History with ${org}", mapping={
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

        if request.POST._items[2][1] == 'create-ticket':
            with all_chats.session.no_autoflush:
                ticket = TicketCollection(request.session).open_ticket(
                    handler_code='CHT', handler_id=chat.id.hex
                )
                TicketMessage.create(ticket, request, 'opened')

                send_ticket_mail(
                    request=request,
                    template='mail_turned_chat_into_ticket.pt',
                    subject=_("Your Chat has been turned into a ticket"),
                    receivers=(chat.email, ),
                    ticket=ticket,
                    content={
                        'model': self,
                        'ticket': ticket,
                        'chat': chat,
                        'organisation': request.app.org.title,
                    }
                )

    return {
        'title': _('Chats'),
        'form': form,
        'layout': StaffChatLayout(self, request),
        'user': user,
        'open_requests': open_requests.all(),
        'active_chats': active_chats.all(),
        'archived_chats': archived_chats.all()
    }


@TownApp.html(
    model=ChatCollection,
    template='chats_archive.pt',
    name='archive',
    permission=Private)
def view_chats_archive(self, request):

    user = request.current_user
    all_chats = ChatCollection(request.session).query()
    archived_chats = all_chats.filter(Chat.active == False)

    return {
        'title': _('Archived Chats'),
        'layout': StaffChatLayout(self, request),
        'user': user,
        'archived_chats': archived_chats.all()
    }


@TownApp.form(
    model=ChatCollection,
    template='form.pt',
    name='initiate',
    permission=Public,
    form=ChatInitiationForm)
def view_chat_form(self: ChatCollection, request, form):

    if not request.app.settings.org.chat_open(
        request
    ) and not request.is_manager:
        raise HTTPForbidden()

    active_chat_id = request.browser_session.get('active_chat_id')
    if active_chat_id and (chat := self.by_id(active_chat_id)) and chat.active:
        return redirect(request.link(chat))

    if form.submitted(request):
        chat = self.add(
            form.name.data,
            form.email.data,
            form.topic.data
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
    permission=Public,)
def view_customer_chat(self, request):

    active_chat_id = request.browser_session.get('active_chat_id')
    if not request.is_manager and self.id != active_chat_id:
        raise HTTPForbidden()

    return {
        'title': _('Chat Customer'),
        'layout': ClientChatLayout(self, request),
        'chat': self,
        'customer_name': self.customer_name
    }
