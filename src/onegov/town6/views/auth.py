""" The authentication views. """

from onegov.core.security import Public
from onegov.org.auth import MTANAuth
from onegov.org.forms import MTANForm, RequestMTANForm
from onegov.org.views.auth import (
    handle_login, handle_registration, handle_password_reset,
    handle_password_reset_request, handle_request_mtan,
    handle_authenticate_mtan
)
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout

from onegov.user import Auth

from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestPasswordResetForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(model=Auth, name='login', template='login.pt', permission=Public,
              form=LoginForm)
def town_handle_login(
    self: Auth,
    request: 'TownRequest',
    form: LoginForm
) -> 'RenderData | Response':
    """ Handles the login requests. """

    return handle_login(self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='register', template='form.pt',
              permission=Public, form=RegistrationForm)
def town_handle_registration(
    self: Auth,
    request: 'TownRequest',
    form: RegistrationForm
) -> 'RenderData | Response':
    return handle_registration(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='request-password', template='form.pt',
              permission=Public, form=RequestPasswordResetForm)
def town_handle_password_reset_request(
    self: Auth,
    request: 'TownRequest',
    form: RequestPasswordResetForm
) -> 'RenderData | Response':
    return handle_password_reset_request(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(model=Auth, name='reset-password', template='form.pt',
              permission=Public, form=PasswordResetForm)
def town_handle_password_reset(
    self: Auth,
    request: 'TownRequest',
    form: PasswordResetForm
) -> 'RenderData | Response':
    return handle_password_reset(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=MTANAuth,
    name='request',
    template='form.pt',
    permission=Public,
    form=RequestMTANForm
)
def towm_handle_request_mtan(
    self: MTANAuth,
    request: 'TownRequest',
    form: RequestMTANForm
) -> 'RenderData | Response':
    return handle_request_mtan(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=MTANAuth,
    name='auth',
    template='form.pt',
    permission=Public,
    form=MTANForm
)
def towm_handle_authenticate_mtan(
    self: MTANAuth,
    request: 'TownRequest',
    form: MTANForm
) -> 'RenderData | Response':
    return handle_authenticate_mtan(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )
