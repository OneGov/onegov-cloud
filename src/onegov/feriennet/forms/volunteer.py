from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Email


class VolunteerForm(Form):

    first_name = StringField(
        label=_("First Name"),
        validators=[InputRequired()])

    last_name = StringField(
        label=_("Last Name"),
        validators=[InputRequired()])

    birth_date = DateField(
        label=_("Birthdate"),
        validators=[InputRequired()])

    organisation = StringField(
        label=_("Organisation"))

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 4},
        validators=[InputRequired()])

    zip_code = StringField(
        label=_("Zip Code"),
        validators=[InputRequired()])

    place = StringField(
        label=_("Place"),
        validators=[InputRequired()])

    email = EmailField(
        label=_("E-Mail Address"),
        validators=[InputRequired(), Email()])

    phone = StringField(
        label=_("Phone"),
        validators=[InputRequired()])
