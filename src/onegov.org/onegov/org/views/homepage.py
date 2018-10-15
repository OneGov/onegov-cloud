""" The onegov organisation homepage. """

from morepath import redirect
from onegov.core.security import Public
from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.form import FormCollection
from onegov.org import OrgApp
from onegov.org.homepage_widgets import inject_widget_variables
from onegov.org.layout import DefaultLayout
from onegov.org.models import Organisation
from onegov.org.models import PublicationCollection
from onegov.reservation import ResourceCollection


def redirect_to(request, target):
    if target == 'directories':
        return redirect(request.class_link(DirectoryCollection))

    if target == 'events':
        return redirect(request.class_link(OccurrenceCollection))

    if target == 'forms':
        return redirect(request.class_link(FormCollection))

    if target == 'publications':
        return redirect(request.class_link(PublicationCollection))

    if target == 'reservations':
        return redirect(request.class_link(ResourceCollection))


@OrgApp.html(model=Organisation, template='homepage.pt', permission=Public)
def view_org(self, request):
    """ Renders the org's homepage. """

    # the homepage can optionally be used as a jump-pad to redirect to
    # sub-part of the organisation -> this is useful if only one specific
    # module is used (e.g. only reservations)
    redirect = redirect_to(request, request.app.org.redirect_homepage_to)

    if redirect:
        return redirect

    layout = DefaultLayout(self, request)

    default = {
        'layout': layout,
        'title': self.title
    }

    structure = self.meta.get('homepage_structure')
    return inject_widget_variables(layout, structure, default)
