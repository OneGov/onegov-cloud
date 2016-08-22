from onegov.form import Form
from onegov.org import _
from onegov.user import UserCollection
from wtforms import HiddenField, StringField, PasswordField, validators


class RequestPasswordResetForm(Form):
    """ Defines the password reset request form for onegov org. """

    email = StringField(
        _("Email Address"),
        [validators.InputRequired(), validators.Email()]
    )

    def get_token(self, request):
        """ Returns the user and a token for the given username to reset the
        password. If the username is not found, (None, None) is returned.

        """
        users = UserCollection(request.app.session())
        user = users.by_username(self.email.data)
        token = None

        if user is not None:
            modified = user.modified.isoformat() if user.modified else ''
            token = request.new_url_safe_token({
                'username': user.username,
                'modified': modified
            })
        return user, token


class PasswordResetForm(Form):
    """ Defines the password reset form for onegov org. """

    email = StringField(
        _("Email Address"),
        [validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        _("New Password"),
        [validators.InputRequired(), validators.Length(min=8)]
    )
    token = HiddenField()

    def update_password(self, request):
        """ Updates the password using the form data (if permitted to do so).

        Returns True if successful, False if not successful.
        """
        data = request.load_url_safe_token(self.token.data, max_age=86400)

        if not data:
            return False

        if not data.get('username') == self.email.data:
            return False

        users = UserCollection(request.app.session())
        user = users.by_username(self.email.data)

        if not user:
            return False

        modified = user.modified.isoformat() if user.modified else ''

        if modified != data['modified']:
            return False

        user.password = self.password.data

        return True
