from onegov.core.security import Public
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.user import Auth
from onegov.user.forms import LoginForm
from onegov.org.views.auth import handle_login as handle_login_base


@TranslatorDirectoryApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=LoginForm
)
def handle_login(self, request, form):
    # custom default redirect
    if self.to == '/':
        self.to = '/translators'

    return handle_login_base(self, request, form)
