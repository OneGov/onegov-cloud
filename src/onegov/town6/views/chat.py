from onegov.core.security import Public
from onegov.org.views.chat import view_chat
from onegov.town6 import TownApp

from onegov.chat.collections import ChatCollection
from onegov.town6.layout import DefaultLayout


@TownApp.html(model=ChatCollection, template='chats.pt', permission=Public)
def town_view_chat(self, request):
    return view_chat(self, request, DefaultLayout(self, request))
