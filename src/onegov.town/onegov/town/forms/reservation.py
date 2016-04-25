from onegov.form import Form
from onegov.town import _
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, InputRequired


# include all fields used below so we can filter them out
# when we merge this form with the custom form definition
RESERVED_FIELDS = ['email']


class ReservationForm(Form):

    reserved_fields = RESERVED_FIELDS

    email = EmailField(
        label=_("E-Mail"),
        validators=[InputRequired(), Email()]
    )
