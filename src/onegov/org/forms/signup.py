from onegov.form import Form
from onegov.org import _
from wtforms import StringField, validators


class SignupForm(Form):

    address = StringField(
        label=_("E-Mail Address"),
        validators=[validators.InputRequired(), validators.Email()]
    )
