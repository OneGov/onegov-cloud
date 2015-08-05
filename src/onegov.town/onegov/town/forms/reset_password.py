import morepath

from onegov.form import Form
from onegov.town import _
from onegov.user import UserCollection
from wtforms import HiddenField, StringField, PasswordField, validators


class RequestPasswordResetForm(Form):
    """ Defines the password reset request form for onegov town. """

    email = StringField(
        _(u"Email Address"),
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
    """ Defines the password reset form for onegov town. """

    email = StringField(
        _(u"Email Address"),
        [validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(
        _(u"New Password"),
        [validators.InputRequired(), validators.Length(min=8)]
    )
    token = HiddenField()

    def get_identity(self, request):
        """ Returns the given user by username, token and the new password.
        If the username is not found or the token invalid, None is returned.

        """
        data = request.load_url_safe_token(self.token.data, max_age=86400)
        if data and data['username'] == self.email.data:
            users = UserCollection(request.app.session())
            user = users.by_username(self.email.data)
            if user:
                modified = user.modified.isoformat() if user.modified else ''
                if modified == data['modified']:
                    user.password = self.password.data
                    return morepath.Identity(
                        userid=user.username,
                        role=user.role,
                        application_id=request.app.application_id
                    )

        return None
