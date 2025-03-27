from __future__ import annotations

from onegov.core.security import Public
from onegov.org.models import News, NewsCollection, Topic
from onegov.org.views.page import view_topic, view_news, view_news_collection
from onegov.town6 import TownApp
from onegov.town6.layout import PageLayout, NewsLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=Topic, template='topic.pt', permission=Public)
def town_view_topic(
    self: Topic,
    request: TownRequest
) -> RenderData | Response:
    return view_topic(self, request, PageLayout(self, request))


@TownApp.html(model=NewsCollection, template='news.pt', permission=Public)
def town_view_news_collection(
    self: NewsCollection, request: TownRequest
) -> RenderData | Response:
    return view_news_collection(self, request, NewsLayout(self.root, request))


@TownApp.html(model=News, template='news.pt', permission=Public)
def town_view_news(
    self: News, request: TownRequest
) -> RenderData | Response:
    return view_news(self, request, NewsLayout(self, request))
