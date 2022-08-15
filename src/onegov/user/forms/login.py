from onegov.form import Form
from onegov.user import _
from wtforms.fields import PasswordField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class LoginForm(Form):
    """ A generic login form for onegov.user """

    username = StringField(
        label=_("E-Mail Address"),
        validators=[InputRequired()],
        render_kw={'autofocus': True}
    )
    password = PasswordField(
        label=_("Password"),
        validators=[InputRequired()],
        render_kw={'autocomplete': 'current-password'}
    )
    yubikey = StringField(
        label=_("YubiKey"),
        description=_("Plug your YubiKey into a USB slot and press it."),
        render_kw={'autocomplete': 'off'}
    )

    @property
    def login_data(self):
        """ Returns the data required to be passed to the
        :class:`onegov.user.auth.Auth` methods.

        """

        # the yubikey field may be removed downstream - username and password
        # however *must* be there
        yubikey = getattr(self, 'yubikey', None)
        yubikey = yubikey and (yubikey.data or '').strip() or None

        return {
            'username': self.username.data,
            'password': self.password.data,
            'second_factor': yubikey
        }
