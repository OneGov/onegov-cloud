from onegov.core.security import Public, Private
from onegov.org import _
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.town6 import TownApp
from onegov.town6.layout import HomepageLayout


@TownApp.html(model=Organisation, template='homepage.pt', permission=Public)
def town_view_org(self, request):
    return view_org(self, request, HomepageLayout(self, request))


@TownApp.html(
    model=Organisation,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_pages_sort(self, request, layout=None):
    layout = layout or HomepageLayout(self, request)

    return {
        'title': _("Sort"),
        'layout': layout,
        'page': self,
        'pages': layout.root_pages
    }
