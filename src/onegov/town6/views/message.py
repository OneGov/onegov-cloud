from onegov.chat import MessageCollection
from onegov.core.security import Private

from onegov.org.views.message import view_messages
from onegov.town6 import TownApp
from onegov.town6.layout import MessageCollectionLayout


@TownApp.html(
    model=MessageCollection,
    permission=Private,
    template='timeline.pt'
)
def town_view_messages(self, request):
    return view_messages(self, request, MessageCollectionLayout(self, request))
