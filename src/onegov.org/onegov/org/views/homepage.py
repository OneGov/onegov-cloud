""" The onegov organisation homepage. """

from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.org.homepage_widgets import inject_widget_variables


@OrgApp.html(model=Organisation, template='homepage.pt', permission=Public)
def view_org(self, request):
    """ Renders the org's homepage. """

    layout = DefaultLayout(self, request)

    default = {
        'layout': layout,
        'title': self.name
    }

    structure = self.meta.get('homepage_structure')
    return inject_widget_variables(layout, structure, default)
