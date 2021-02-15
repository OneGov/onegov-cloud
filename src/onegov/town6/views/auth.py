""" The authentication views. """

from onegov.core.security import Public, Personal
from onegov.org.views.auth import (
    handle_login, handle_registration, do_logout,
    handle_password_reset_request, handle_password_reset
)
from onegov.town6 import TownApp

from onegov.user import Auth

from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestPasswordResetForm


@TownApp.form(model=Auth, name='login', template='login.pt', permission=Public,
              form=LoginForm)
def town_handle_login(self, request, form):
    """ Handles the login requests. """

    return handle_login(self, request, form)


@TownApp.form(model=Auth, name='register', template='form.pt',
              permission=Public, form=RegistrationForm)
def town_handle_registration(self, request, form):
    return handle_registration(self, request, form)


@TownApp.html(model=Auth, name='logout', permission=Personal)
def view_logout(self, request):
    return do_logout(self, request)


@TownApp.form(model=Auth, name='request-password', template='form.pt',
              permission=Public, form=RequestPasswordResetForm)
def town_handle_password_reset_request(self, request, form):
    return handle_password_reset_request(self, request, form)


@TownApp.form(model=Auth, name='reset-password', template='form.pt',
              permission=Public, form=PasswordResetForm)
def town_handle_password_reset(self, request, form):
    return handle_password_reset(self, request, form)
