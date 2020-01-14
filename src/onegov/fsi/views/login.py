from onegov.core.security import Public
from onegov.fsi import _
from onegov.fsi.app import FsiApp
from onegov.org.views.auth import handle_login as handle_login_base
from onegov.user import Auth
from onegov.user.forms import LoginForm


@FsiApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=LoginForm)
def handle_login(self, request, form):

    # custom default redirect
    if self.to == '/':
        self.to = '/fsi/courses'

    # custom username handle
    form.username.label.text = request.translate(
        _("E-Mail Address / Username / Shortcut"))

    return handle_login_base(self, request, form)
