from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.org import _
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class SignupForm(Form):

    address = StringField(
        label=_("E-Mail Address"),
        validators=[InputRequired(), Email()]
    )

    name = HoneyPotField()
