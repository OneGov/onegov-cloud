from onegov.agency import AgencyApp
from onegov.agency.layout import PageLayout
from onegov.core.security import Public
from onegov.org.models import Topic
from onegov.org.views.page import view_topic as view_topic_base


@AgencyApp.html(model=Topic, template='topic.pt', permission=Public)
def view_topic(self, request):
    layout = PageLayout(self, request)
    return view_topic_base(self, request, layout)
