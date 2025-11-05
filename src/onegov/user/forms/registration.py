from __future__ import annotations

from onegov.form import Form
from onegov.form.validators import ValidPassword
from onegov.user import _
from onegov.user.collections import MIN_PASSWORD_LENGTH
from wtforms.fields import PasswordField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import InputRequired
from wtforms.validators import Length


class RegistrationForm(Form):
    """ A generic registration form for onegov.user """

    username = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()]
    )

    password = PasswordField(
        label=_('Password'),
        validators=[
            InputRequired(),
            ValidPassword(MIN_PASSWORD_LENGTH, _(
                'The password must be at least ten characters long'
            ))
        ]
    )

    confirm = PasswordField(
        label=_('Password Confirmation'),
        validators=[InputRequired(), EqualTo(
            'password', message=_('Passwords must match')
        )]
    )

    # To avoid the most basic spam bots we present a field which the user
    # should not fill. We'll actually hide this field from the user. Bots
    # tend to fill out all fields. If they do they won't succeed.
    #
    # This however won't deterr a targeted attack. We'll have to see if we
    # need a more sophisticated approach in the future.
    roboter_falle = StringField(
        label=_('Please leave this field empty'),
        validators=[Length(max=0, message=_(
            'The field is not empty'
        ))]
    )
