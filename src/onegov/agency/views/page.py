from __future__ import annotations

from onegov.agency import AgencyApp
from onegov.agency.layout import TopicLayout
from onegov.core.security import Public
from onegov.org.models import Topic
from onegov.org.views.page import view_topic as view_topic_base


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.core.types import RenderData
    from webob import Response


@AgencyApp.html(model=Topic, template='topic.pt', permission=Public)
def view_topic(
    self: Topic,
    request: AgencyRequest
) -> RenderData | Response:
    layout = TopicLayout(self, request)
    return view_topic_base(self, request, layout)
