from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import PhoneNumberField
from wtforms import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class EmailSubscriptionForm(Form):

    email = StringField(
        label=_("Email"),
        validators=[
            InputRequired(),
            Email()
        ]
    )


class SmsSubscriptionForm(Form):

    phone_number = PhoneNumberField(
        label=_("Phone number"),
        description="+41791112233",
        validators=[
            InputRequired(),
        ],
    )
