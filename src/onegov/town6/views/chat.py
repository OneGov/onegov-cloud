from onegov.core.security import Private, Public
from onegov.town6 import TownApp
from morepath import redirect

from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.chat.forms import ChatInitiationForm
from onegov.town6.layout import StaffChatLayout, ClientChatLayout
from onegov.town6.layout import DefaultLayout
from webob.exc import HTTPForbidden


@TownApp.html(
    model=ChatCollection,
    template='chats_staff.pt',
    permission=Private,)
def view_chats_staff(self, request):

    user = request.current_user

    all_chats = ChatCollection(request.session).query()
    open_requests = all_chats.filter(Chat.user_id == None)
    active_chats = all_chats.filter(Chat.user_id == user.id).filter(
        Chat.active == True)
    archived_chats = all_chats.filter(
        Chat.active == False)

    return {
        'title': 'Chat Staff',
        'layout': StaffChatLayout(self, request),
        'user': user,
        'open_requests': open_requests.all(),
        'active_chats': active_chats.all(),
        'archived_chats': archived_chats.all()
    }


@TownApp.form(
    model=ChatCollection,
    template='form.pt',
    name='initiate',
    permission=Public,
    form=ChatInitiationForm)
def view_chat_form(self:ChatCollection, request, form):

    active_chat_id = request.browser_session.get('active_chat_id')
    if active_chat_id and (chat := self.by_id(active_chat_id)) and chat.active:
        return redirect(request.link(chat))

    if form.submitted(request):
        chat = self.add(
            form.name.data,
            form.email.data,
        )
        request.browser_session['active_chat_id'] = chat.id
        return redirect(request.link(chat))

    return {
        'title': 'Chat Customer',
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
        'title': 'Chat Customer',
        'layout': ClientChatLayout(self, request),
        'chat': self,
        'customer_name': self.customer_name
    }
