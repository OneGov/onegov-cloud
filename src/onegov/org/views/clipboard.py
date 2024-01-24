import morepath

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.models import Clipboard


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.view(model=Clipboard, permission=Private)
def copy_to_clipboard(self: Clipboard, request: 'OrgRequest') -> 'Response':
    self.store_in_session()
    request.success(_("A link was added to the clipboard"))
    return morepath.redirect(request.referer or request.transform('/'))
