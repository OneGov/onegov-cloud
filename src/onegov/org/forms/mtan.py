from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import PhoneNumberField
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

    def on_request(self):
        # pre-fill mTAN when it is submitted in a GET request
        request = self.meta.request
        if not request.POST and 'tan' in request.GET:
            self.tan.data = request.GET['tan']


class RequestMTANForm(Form):

    phone_number = PhoneNumberField(
        label=_("Phone number"),
        description="+41791112233",
        validators=[
            InputRequired(),
        ],
        render_kw={
            'autocomplete': 'tel',
        }
    )

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )
