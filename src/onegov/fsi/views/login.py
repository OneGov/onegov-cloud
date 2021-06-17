from onegov.core.security import Public
from onegov.fsi import _
from onegov.fsi.app import FsiApp
from onegov.org.views.auth import handle_login as handle_login_base
from onegov.user import Auth
from onegov.user.forms import LoginForm


class FsiLoginForm(LoginForm):

    @property
    def login_data(self):
        """
        Skips auth providers for school users are just indexed by the LDAP but
        not can bot be logged in to. The are authenticated with the user and
        password in our database, so we pass skip_providers to the login data.
        """
        login_data = super().login_data
        username = self.username.data
        if not username or '@' not in username:
            return login_data
        if username.endswith('@zg.ch'):
            return login_data

        # Make sure the username is lowered
        login_data['username'] = login_data['username'].lower()

        return {
            'skip_providers': True,
            **login_data
        }


@FsiApp.form(model=Auth, name='login', template='login.pt', permission=Public,
             form=FsiLoginForm)
def handle_login(self, request, form):

    # custom default redirect
    if self.to == '/':
        self.to = '/fsi/courses'

    # custom username handle
    form.username.label.text = request.translate(
        _("E-Mail Address / Username / Shortcut"))

    return handle_login_base(self, request, form)
