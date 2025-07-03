""" The authentication views. """
from __future__ import annotations

from onegov.core.security import Public
from onegov.org.auth import MTANAuth
from onegov.org.forms import CitizenLoginForm, ConfirmCitizenLoginForm
from onegov.org.forms import PublicMTANForm, PublicRequestMTANForm
from onegov.org.views.auth import (
    handle_login, handle_registration, handle_password_reset,
    handle_password_reset_request, handle_mtan_second_factor,
    handle_mtan_second_factor_setup, handle_request_mtan,
    handle_authenticate_mtan, handle_totp_second_factor,
    handle_citizen_login, handle_confirm_citizen_login
)
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout
from onegov.user import Auth
from onegov.user.forms import LoginForm
from onegov.user.forms import MTANForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestMTANForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.forms import TOTPForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=Auth,
    name='login',
    template='login.pt',
    permission=Public,
    form=LoginForm
)
def town_handle_login(
    self: Auth,
    request: TownRequest,
    form: LoginForm
) -> RenderData | Response:
    """ Handles the login requests. """

    return handle_login(self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=Auth,
    name='register',
    template='form.pt',
    permission=Public,
    form=RegistrationForm
)
def town_handle_registration(
    self: Auth,
    request: TownRequest,
    form: RegistrationForm
) -> RenderData | Response:
    return handle_registration(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=Auth,
    name='request-password',
    template='form.pt',
    permission=Public,
    form=RequestPasswordResetForm
)
def town_handle_password_reset_request(
    self: Auth,
    request: TownRequest,
    form: RequestPasswordResetForm
) -> RenderData | Response:
    return handle_password_reset_request(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=Auth,
    name='reset-password',
    template='form.pt',
    permission=Public,
    form=PasswordResetForm
)
def town_handle_password_reset(
    self: Auth,
    request: TownRequest,
    form: PasswordResetForm
) -> RenderData | Response:
    return handle_password_reset(
        self, request, form, DefaultLayout(self, request))


@TownApp.form(
    model=Auth,
    name='mtan',
    template='form.pt',
    permission=Public,
    form=MTANForm
)
def town_handle_mtan_second_factor(
    self: Auth,
    request: TownRequest,
    form: MTANForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    return handle_mtan_second_factor(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=Auth,
    name='mtan-setup',
    template='form.pt',
    permission=Public,
    form=RequestMTANForm
)
def town_handle_mtan_second_factor_setup(
    self: Auth,
    request: TownRequest,
    form: RequestMTANForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    return handle_mtan_second_factor_setup(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=Auth,
    name='totp',
    template='form.pt',
    permission=Public,
    form=TOTPForm
)
def town_handle_totp_second_factor(
    self: Auth,
    request: TownRequest,
    form: TOTPForm,
    layout: DefaultLayout | None = None
) -> RenderData | Response:
    return handle_totp_second_factor(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=MTANAuth,
    name='request',
    template='form.pt',
    permission=Public,
    form=PublicRequestMTANForm
)
def town_handle_request_mtan(
    self: MTANAuth,
    request: TownRequest,
    form: PublicRequestMTANForm
) -> RenderData | Response:
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
    form=PublicMTANForm
)
def town_handle_authenticate_mtan(
    self: MTANAuth,
    request: TownRequest,
    form: PublicMTANForm
) -> RenderData | Response:
    return handle_authenticate_mtan(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=Auth,
    name='citizen-login',
    template='form.pt',
    permission=Public,
    form=CitizenLoginForm
)
def town_handle_citizen_login(
    self: Auth,
    request: TownRequest,
    form: CitizenLoginForm
) -> RenderData | Response:
    return handle_citizen_login(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )


@TownApp.form(
    model=Auth,
    name='confirm-citizen-login',
    template='form.pt',
    permission=Public,
    form=ConfirmCitizenLoginForm
)
def town_handle_confirm_citizen_login(
    self: Auth,
    request: TownRequest,
    form: ConfirmCitizenLoginForm
) -> RenderData | Response:
    return handle_confirm_citizen_login(
        self,
        request,
        form,
        DefaultLayout(self, request)
    )
