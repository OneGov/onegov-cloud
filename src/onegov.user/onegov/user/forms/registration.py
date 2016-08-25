from onegov.core.crypto import random_token
from onegov.form import Form
from onegov.user import _
from onegov.user.collection import UserCollection
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
            validators.Length(min=8, message=_(
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
            "Please leave this field empty"
        ))]
    )

    def create_user(self, session, role='member'):
        """ Creates the user using the information on the form.

        The so created user needs to activated with a token before it becomes
        active. Use the activation_token in the data dictionary together
        with the :meth:`onegov.user.collections.activate_with_token`
        function.

        """

        users = UserCollection(session)

        if users.by_username(self.username.data):
            return False

        return users.add(
            username=self.username.data,
            password=self.password.data,
            role=role,
            data={
                'activation_token': random_token()
            },
            active=False
        )
