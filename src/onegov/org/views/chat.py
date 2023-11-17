from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.org.layout import DefaultLayout
from onegov.chat.collections import ChatCollection


@OrgApp.html(model=ChatCollection, template='chats.pt',
             permission=Public)
def view_chat(self, request, layout=None):

    return {
        'title': 'Chat',
        'layout': layout or DefaultLayout(self, request),
    }
