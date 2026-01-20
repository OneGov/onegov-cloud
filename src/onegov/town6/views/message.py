from __future__ import annotations

from onegov.chat import Message, MessageCollection
from onegov.core.security import Private

from onegov.org.views.message import view_messages
from onegov.town6 import TownApp
from onegov.town6.layout import MessageCollectionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=MessageCollection,
    permission=Private,
    template='timeline.pt'
)
def town_view_messages(
    self: MessageCollection[Message],
    request: TownRequest
) -> RenderData:
    return view_messages(self, request, MessageCollectionLayout(self, request))
