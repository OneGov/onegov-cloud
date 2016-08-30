from onegov.form import Form
from onegov.user import _
from wtforms import StringField, PasswordField, validators


class LoginForm(Form):
    """ A generic login form for onegov.user """

    username = StringField(
        label=_("E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        label=_("Password"),
        validators=[validators.InputRequired()]
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
        yubikey = yubikey and yubikey.data.strip() or None

        return {
            'username': self.username.data,
            'password': self.password.data,
            'second_factor': yubikey
        }
