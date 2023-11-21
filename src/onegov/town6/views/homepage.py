from onegov.core.security import Public, Private
from onegov.org import _
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.chat.collections import ChatCollection
from onegov.town6 import TownApp
from onegov.town6.layout import HomepageLayout


@TownApp.html(model=Organisation, template='homepage.pt', permission=Public)
def town_view_org(self, request):
    view = view_org(self, request, HomepageLayout(self, request))
    # catch redirect
    from webob.exc import HTTPFound
    if isinstance(view, HTTPFound):
        return view

    chats = ChatCollection(request.session)
    chat_link = request.link(chats, 'initiate')
    view['chat_link'] = chat_link

    return view


@TownApp.html(
    model=Organisation,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_pages_sort(self, request, layout=None):
    layout = layout or HomepageLayout(self, request)

    return {
        'title': _("Sort"),
        'layout': layout,
        'page': self,
        'pages': layout.root_pages
    }
