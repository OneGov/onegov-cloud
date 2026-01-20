""" The onegov organisation homepage. """
from __future__ import annotations

from morepath import redirect
from onegov.core.security import Public, Private
from onegov.core.widgets import inject_variables
from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.form import FormCollection
from onegov.org import _
from onegov.org import OrgApp
from onegov.org.layout import HomepageLayout
from onegov.org.models import Organisation
from onegov.org.models import PublicationCollection
from onegov.reservation import ResourceCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.layout import Layout
    from onegov.org.request import OrgRequest
    from webob import Response


def redirect_to(
    request: OrgRequest,
    target: str | None,
    path: str | None
) -> Response | None:
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

    if target == 'path' and path:
        return redirect(request.class_link(Organisation) + path.lstrip('/'))

    return None


@OrgApp.html(model=Organisation, template='homepage.pt', permission=Public)
def view_org(
    self: Organisation,
    request: OrgRequest,
    layout: Layout | None = None
) -> RenderData | Response:
    """ Renders the org's homepage. """

    # the homepage can optionally be used as a jump-pad to redirect to
    # sub-part of the organisation -> this is useful if only one specific
    # module is used (e.g. only reservations)
    redirect = redirect_to(
        request,
        request.app.org.redirect_homepage_to,
        request.app.org.redirect_path)

    if redirect:
        return redirect

    layout = layout or HomepageLayout(self, request)

    default = {
        'layout': layout,
        'title': self.title
    }

    structure = self.meta.get('homepage_structure')
    widgets = request.app.config.homepage_widget_registry.values()
    return inject_variables(widgets, layout, structure, default)


@OrgApp.html(
    model=Organisation,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_pages_sort(
    self: Organisation,
    request: OrgRequest,
    layout: HomepageLayout | None = None
) -> RenderData:

    layout = layout or HomepageLayout(self, request)

    return {
        'title': _('Sort'),
        'layout': layout,
        'page': self,
        'pages': layout.root_pages
    }
