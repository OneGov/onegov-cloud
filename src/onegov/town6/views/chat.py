from onegov.core.security import Private, Public
from onegov.town6 import TownApp
from morepath import redirect

from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.chat.forms import ChatInitiationForm
from onegov.town6.layout import ChatLayout
from webob.exc import HTTPForbidden


@TownApp.html(
    model=ChatCollection,
    template='chats_staff.pt',
    permission=Private,)
def view_chats_staff(self, request):

    return {
        'title': 'Chat Staff',
        'layout': ChatLayout(self, request),
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
        'layout': ChatLayout(self, request),
        'form': form
    }


@TownApp.html(
    model=Chat,
    template='chats_customer.pt',
    permission=Public,)
def view_customer_chat(self, request):

    active_chat_id = request.browser_session.get('active_chat_id')
    if not request.is_manager and self.id != active_chat_id:
        raise HTTPForbidden()

    return {
        'title': 'Chat Customer',
        'layout': ChatLayout(self, request),
    }
