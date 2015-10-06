""" The authentication views. """

from onegov.core.security import Public, Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import Layout
from onegov.user import Auth
from onegov.user.forms import LoginForm


@ElectionDayApp.form(model=Auth, name='login', template='form.pt',
                     permission=Public, form=LoginForm)
def handle_login(self, request, form):
    """ Handles the login requests. """

    if form.submitted(request):
        response = self.login_to(request=request, **form.login_data)
        form.error_message = _("Wrong username or password")
    else:
        response = None

    return response or {
        'layout': Layout(self, request),
        'title': _("Login"),
        'form': form
    }


@ElectionDayApp.html(model=Auth, name='logout', permission=Private)
def view_logout(self, request):
    """ Handles the logout requests. """

    return self.logout_to(request)
