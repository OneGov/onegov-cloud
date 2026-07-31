from __future__ import annotations

from onegov.core.security import Private
from onegov.org.models import Organisation
from onegov.org.views.topic_chart import (
    view_topic_chart)
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=Organisation,
    name='topic-chart',
    template='topic_chart.pt',
    permission=Private
)
def town_view_topic_chart(
    self: Organisation,
    request: TownRequest,
    layout: DefaultLayout | None = None
) -> RenderData:
    return view_topic_chart(
        self, request, layout or DefaultLayout(self, request)
    )
