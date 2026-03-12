from __future__ import annotations

from onegov.form import Form
from onegov.user import _
from wtforms.fields import PasswordField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import NotRequired
    from typing import TypedDict

    class LoginData(TypedDict):
        username: str
        password: str
        second_factor: str | None
        skip_providers: NotRequired[bool]


class LoginForm(Form):
    """ A generic login form for onegov.user """

    username = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired()],
        render_kw={
            'autofocus': True,
            'autocomplete': 'username'
        },
    )
    password = PasswordField(
        label=_('Password'),
        validators=[InputRequired()],
        render_kw={'autocomplete': 'current-password'}
    )
    yubikey = StringField(
        label=_('YubiKey'),
        description=_('Plug your YubiKey into a USB slot and press it.'),
        render_kw={'autocomplete': 'off'}
    )

    @property
    def login_data(self) -> LoginData:
        """ Returns the data required to be passed to the
        :class:`onegov.user.auth.Auth` methods.

        """

        # the yubikey field may be removed downstream - username and password
        # however *must* be there
        yubikey = getattr(self, 'yubikey', None)
        yubikey = yubikey and (yubikey.data or '').strip() or None

        return {
            # these should be set if the form has been validated
            # but the type checker can't know that, plus someone
            # might call this prior to validation, it should still
            # work in that case
            'username': self.username.data or '',
            'password': self.password.data or '',
            'second_factor': yubikey
        }
