from onegov.translator_directory import _
from onegov.core.security import Public
from onegov.fsi.views.login import FsiLoginForm
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.user import Auth
from onegov.org.views.auth import handle_login as handle_login_base


@TranslatorDirectoryApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=FsiLoginForm
)
def handle_login(self, request, form):
    # custom default redirect
    if self.to == '/':
        self.to = '/translators'

    # custom username handle
    form.username.label.text = request.translate(
        _("E-Mail Address / Username / Shortcut"))

    return handle_login_base(self, request, form)
