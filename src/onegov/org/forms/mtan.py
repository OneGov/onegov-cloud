from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import PhoneNumberField
from onegov.form.validators import ValidPhoneNumber
from onegov.org import _
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class MTANForm(Form):
    """ Defines the settings form for user profiles. """

    tan = StringField(
        label=_("mTAN"),
        # the TAN alphabet is all uppercase so we're nice and just
        # auto uppercase the entered data, as well as strip any
        # whitespace introduced through copy-pasta
        filters=[lambda x: '' if x is None else x, str.strip, str.upper],
        validators=[InputRequired()]
    )

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )

    def on_request(self) -> None:
        # pre-fill mTAN when it is submitted in a GET request
        if not self.request.POST and 'tan' in self.request.GET:
            self.tan.data = self.request.GET['tan']


class RequestMTANForm(Form):

    phone_number = PhoneNumberField(
        label=_("Phone number"),
        description="+41791112233",
        validators=(
            InputRequired(),
            # FIXME: Make configurable, for now we just use a sane default for
            #        Switzerland, including its neighbouring countries
            ValidPhoneNumber(country_whitelist={
                'CH', 'AT', 'DE', 'FR', 'IT', 'LI'
            })
        ),
        render_kw={
            'autocomplete': 'tel',
        }
    )

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )
