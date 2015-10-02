
import morepath

from onegov.form import Form
from onegov.user import _, UserCollection
from wtforms import StringField, PasswordField, validators


class LoginForm(Form):
    """ A generic login form for onegov.user """

    email = StringField(
        _("Email Address"),
        [validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(_("Password"), [validators.InputRequired()])

    def get_identity(self, request):
        """ Returns the identity if the username and password match. If they
        don't match, None is returned.

        """
        users = UserCollection(request.app.session())
        user = users.by_username_and_password(
            self.email.data, self.password.data
        )

        if user is None:
            return None
        else:
            return morepath.Identity(
                userid=user.username,
                role=user.role,
                application_id=request.app.application_id
            )
