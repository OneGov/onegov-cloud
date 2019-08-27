import morepath

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.models import Clipboard


@OrgApp.view(model=Clipboard, permission=Private)
def copy_to_clipboard(self, request):
    self.store_in_session()
    request.success(_("A link was added to the clipboard"))
    return morepath.redirect(request.referer)
