import phonenumbers

from onegov.election_day import _
from onegov.election_day.forms.validators import ValidPhoneNumber
from onegov.form import Form
from wtforms import StringField
from wtforms.validators import InputRequired


class SubscribeForm(Form):

    phone_number = StringField(
        label=_("Phone number"),
        description="+41791112233",
        validators=[
            InputRequired(),
            ValidPhoneNumber()
        ],
    )

    @property
    def formatted_phone_number(self):
        try:
            return phonenumbers.format_number(
                phonenumbers.parse(self.phone_number.data, 'CH'),
                phonenumbers.PhoneNumberFormat.E164
            )
        except:
            return None
