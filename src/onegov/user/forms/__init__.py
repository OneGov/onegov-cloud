from __future__ import annotations

from onegov.user.forms.group import UserGroupForm
from onegov.user.forms.login import LoginForm
from onegov.user.forms.mtan import MTANForm
from onegov.user.forms.mtan import RequestMTANForm
from onegov.user.forms.registration import RegistrationForm
from onegov.user.forms.reset_password import PasswordResetForm
from onegov.user.forms.reset_password import RequestPasswordResetForm
from onegov.user.forms.signup_link import SignupLinkForm
from onegov.user.forms.totp import TOTPForm

__all__ = [
    'LoginForm',
    'MTANForm',
    'PasswordResetForm',
    'RegistrationForm',
    'RequestMTANForm',
    'RequestPasswordResetForm',
    'SignupLinkForm',
    'UserGroupForm',
    'TOTPForm'
]
