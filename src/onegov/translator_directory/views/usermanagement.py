from onegov.core.security import Secret
from onegov.org.views.usermanagement import get_manage_user_form
from onegov.org.views.usermanagement import handle_manage_user
from onegov.org.views.usermanagement import view_usermanagement
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.user import ManageUserFormCustom
from onegov.user import User
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


def get_manage_user_form_custom(self, request):
    return get_manage_user_form(self, request, base=ManageUserFormCustom)


@TranslatorDirectoryApp.form(
    model=User,
    template='form.pt',
    form=get_manage_user_form_custom,
    permission=Secret,
    name='edit'
)
def handle_manage_user_custom(self, request, form, layout=None):
    return handle_manage_user(self, request, form)
