from onegov.form import Form
from onegov.user import _
from wtforms import StringField, PasswordField, validators


class LoginForm(Form):
    """ A generic login form for onegov.user """

    username = StringField(
        label=_("Username/E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        label=_("Password"),
        validators=[validators.InputRequired()]
    )

    @property
    def login_data(self):
        """ Returns the data required to be passed to the
        :class:`onegov.user.auth.Auth` methods.

        """

        return {
            'username': self.username.data,
            'password': self.password.data,
        }
