from onegov.form import Form
from onegov.user import _
from onegov.user.collection import UserCollection, MIN_PASSWORD_LENGTH
from wtforms import StringField, PasswordField, validators


class RegistrationForm(Form):
    """ A generic registration form for onegov.user """

    username = StringField(
        label=_("E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )

    password = PasswordField(
        label=_("Password"),
        validators=[
            validators.InputRequired(),
            validators.Length(min=MIN_PASSWORD_LENGTH, message=_(
                "The password must be at least eight characters long"
            ))
        ]
    )

    confirm = PasswordField(
        label=_("Password Confirmation"),
        validators=[validators.InputRequired(), validators.EqualTo(
            'password', message=_("Passwords must match")
        )]
    )

    # To avoid the most basic spam bots we present a field which the user
    # should not fill. We'll actually hide this field from the user. Bots
    # tend to fill out all fields. If they do they won't succeed.
    #
    # This however won't deterr a targeted attack. We'll have to see if we
    # need a more sophisticated approach in the future.
    roboter_falle = StringField(
        label=_("Please leave this field empty"),
        validators=[validators.Length(max=0, message=_(
            "The field is not empty"
        ))]
    )

    def register_user(self, request, role='member'):
        """ Registers the user using the information on the form.

        See :meth:`onegov.user.collections.UserCollection.register_user` for
        more information.

        """

        return UserCollection(request.app.session()).register(
            self.username.data, self.password.data, request)
