<<<<<<< Updated upstream
from onegov.core.security import Public
from onegov.org.views.chat import view_chat
from onegov.town6 import TownApp

from onegov.chat.collections import ChatCollection
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=ChatCollection, template='chats.pt', permission=Public)
def town_view_chat(self, request):
    return view_chat(self, request, DefaultLayout(self, request))
=======
from onegov.core.security import Private
from onegov.town6 import TownApp

from onegov.chat.collections import ChatCollection
from onegov.chat.forms import ChatForm
from onegov.town6.layout import ChatLayout
from onegov.chat.utils import send_message


@TownApp.form(
    model=ChatCollection,
    template='chats.pt',
    permission=Private,
    form=ChatForm)
def view_chat(self, request, form):

    if form.submitted(request):
        text = form.message.data
        send_message(request, 'mol luege', text, '12i oder so')

    return {
        'title': 'Chat',
        'layout': ChatLayout(self, request),
        'form': form
    }
>>>>>>> Stashed changes
