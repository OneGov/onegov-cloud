from onegov.core.security import Public
from onegov.org.views.auth import handle_login as handle_login_base
from onegov.translator_directory import _
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.forms.login import LoginForm
from onegov.user import Auth


@TranslatorDirectoryApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=LoginForm
)
def handle_login(self, request, form):
    # custom username handle
    form.username.label.text = request.translate(
        _("E-Mail Address / Username / Shortcut")
    )

    return handle_login_base(self, request, form)
