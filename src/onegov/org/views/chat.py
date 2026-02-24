from __future__ import annotations

from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.org.layout import DefaultLayout
from onegov.chat.collections import ChatCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.html(model=ChatCollection, template='chats.pt',
             permission=Public)
def view_chat(
    self: ChatCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    return {
        'title': 'Chat',
        'layout': layout or DefaultLayout(self, request),
    }
