from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.org import _
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.chat.collections import ChatCollection
from onegov.town6 import TownApp
from onegov.town6.layout import HomepageLayout
from webob import Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(model=Organisation, template='homepage.pt', permission=Public)
def town_view_org(
    self: Organisation,
    request: TownRequest
) -> RenderData | Response:
    view = view_org(self, request, HomepageLayout(self, request))
    # catch redirect
    if isinstance(view, Response):
        return view
    if self.enable_chat == 'people_chat':
        chats = ChatCollection(request.session)
        chat_link = request.link(chats, 'initiate')
    else:
        chat_link = self.chat_link if self.chat_link else '#'
    view['chat_link'] = chat_link

    return view


@TownApp.html(
    model=Organisation,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_pages_sort(
    self: Organisation,
    request: TownRequest,
    layout: HomepageLayout | None = None
) -> RenderData:
    layout = layout or HomepageLayout(self, request)

    return {
        'title': _('Sort'),
        'layout': layout,
        'page': self,
        'pages': layout.root_pages
    }
