from onegov.core.security import Public
from onegov.org.models import News, Topic
from onegov.org.views.page import view_topic, view_news
from onegov.town6 import TownApp


@TownApp.html(model=Topic, template='topic.pt', permission=Public)
def town_view_topic(self, request):
    return view_topic(self, request)


@TownApp.html(model=News, template='news.pt', permission=Public)
def town_view_news(self, request):
    return view_news(self, request)
