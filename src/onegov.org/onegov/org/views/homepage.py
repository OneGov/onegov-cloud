""" The onegov organisation homepage. """

from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.org.models import Organisation
from onegov.org.layout import DefaultLayout


@OrgApp.html(model=Organisation, template='homepage.pt', permission=Public)
def view_org(self, request):
    """ Renders the org's homepage. """

    layout = DefaultLayout(self, request)

    return {
        'layout': layout,
        'title': self.name,
    }
