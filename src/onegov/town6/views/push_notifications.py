from __future__ import annotations

from onegov.core.security import Private
from onegov.org.models import PushNotificationCollection
from onegov.org.views.push_notifications import view_push_notifications
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=PushNotificationCollection,
    permission=Private,
    template='push_notifications.pt',
)
def town_view_publications(
    self: PushNotificationCollection, request: TownRequest
) -> RenderData:
    return view_push_notifications(self, request, DefaultLayout(self, request))
