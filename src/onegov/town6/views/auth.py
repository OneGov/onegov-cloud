""" The authentication views. """

from onegov.core.security import Public
from onegov.org.views.auth import (
    handle_login, handle_registration, handle_password_reset,
    handle_password_reset_request
)
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout

from onegov.user import Auth

from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestPasswordResetForm


@TownApp.form(model=Auth, name='login', template='login.pt', permission=Public,
              form=LoginForm)
def town_handle_login(self, request, form):
    """ Handles the login requests. """

    return handle_login(self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='register', template='form.pt',
              permission=Public, form=RegistrationForm)
def town_handle_registration(self, request, form):
    return handle_registration(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='request-password', template='form.pt',
              permission=Public, form=RequestPasswordResetForm)
def town_handle_password_reset_request(self, request, form):
    return handle_password_reset_request(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='reset-password', template='form.pt',
              permission=Public, form=PasswordResetForm)
def town_handle_password_reset(self, request, form):
    return handle_password_reset(
        self, request, form, DefaultLayout(self, request))
