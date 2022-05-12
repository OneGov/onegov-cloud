from onegov.core.security import Secret
from onegov.org.views.usermanagement import view_usermanagement
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.user import UserCollection


@TranslatorDirectoryApp.html(
    model=UserCollection,
    template='usermanagement.pt',
    permission=Secret
)
def view_usermanagement_custom(self, request):
    roles = {
        'admin': _("Administrator"),
        'editor': _("Editor"),
        'member': _("Member"),
        'translator': _("Translator"),
    }
    return view_usermanagement(self, request, roles=roles)
