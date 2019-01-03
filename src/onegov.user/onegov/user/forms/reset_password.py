from onegov.form import Form
from onegov.user import _
from onegov.user import UserCollection
from wtforms import HiddenField, StringField, PasswordField, validators


class RequestPasswordResetForm(Form):
    """ A generic password reset request form for onegov.user. """

    email = StringField(
        label=_("E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )


class PasswordResetForm(Form):
    """ A generic password reset form for onegov.user. """

    email = StringField(
        label=_("E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        label=_("New Password"),
        validators=[validators.InputRequired(), validators.Length(min=8)],
        render_kw={'autocomplete': 'new-password'}
    )
    token = HiddenField()

    def update_password(self, request):
        """ Updates the password using the form data (if permitted to do so).

        Returns True if successful, False if not successful.
        """
        data = request.load_url_safe_token(self.token.data, max_age=86400)

        if not data or not data.get('username') or 'modified' not in data:
            return False

        if data['username'].lower() != self.email.data.lower():
            return False

        users = UserCollection(request.session)
        user = users.by_username(self.email.data)

        if not user:
            return False

        modified = user.modified.isoformat() if user.modified else ''
        if modified != data['modified']:
            return False

        user.password = self.password.data

        return True
