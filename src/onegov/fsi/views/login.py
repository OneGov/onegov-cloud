from __future__ import annotations

from onegov.core.security import Public
from onegov.fsi import _
from onegov.fsi.app import FsiApp
from onegov.town6.views.auth import town_handle_login as handle_login_base
from onegov.user import Auth
from onegov.user.forms import LoginForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fsi.request import FsiRequest
    from onegov.user.forms.login import LoginData
    from webob import Response


class FsiLoginForm(LoginForm):

    @property
    def login_data(self) -> LoginData:
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


@FsiApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=FsiLoginForm
)
def handle_login(
    self: Auth,
    request: FsiRequest,
    form: FsiLoginForm
) -> RenderData | Response:

    # custom default redirect
    if self.to == '/':
        self.to = '/fsi/courses'

    # custom username handle
    form.username.label.text = request.translate(
        _('E-Mail Address / Username / Shortcut'))

    return handle_login_base(self, request, form)
