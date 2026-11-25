from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.winterthur import WinterthurApp
from onegov.org.views import directory as base
from onegov.core.security import Public


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.winterthur.request import WinterthurRequest
    from webob import Response


@WinterthurApp.html(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    template='directory.pt'
)
def view_directory(
    self: ExtendedDirectoryEntryCollection,
    request: WinterthurRequest
) -> RenderData | Response:

    # Allows the page embedding the directory in an iframe to deep link
    # into an entry by passing its name: ?redirect=<entry-name>
    name = request.params.get('redirect')
    if isinstance(name, str) and name:
        entry = self.by_name(name)
        if entry is not None and request.is_visible(entry):
            return request.redirect(request.link(entry))

    return base.view_directory(self, request)
