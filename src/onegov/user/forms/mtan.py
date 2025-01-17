from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import PhoneNumberField
from onegov.form.validators import ValidPhoneNumber
from onegov.user import _
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class MTANForm(Form):

    tan = StringField(
        label=_('mTAN'),
        # the TAN alphabet is all uppercase so we're nice and just
        # auto uppercase the entered data, as well as strip any
        # whitespace introduced through copy-pasta
        filters=[lambda x: '' if x is None else x, str.strip, str.upper],
        validators=[InputRequired()]
    )

    def on_request(self) -> None:
        # pre-fill mTAN when it is submitted in a GET request
        if not self.request.POST and 'tan' in self.request.GET:
            self.tan.data = self.request.GET['tan']


class RequestMTANForm(Form):

    phone_number = PhoneNumberField(
        label=_('Phone number'),
        description='+41791112233',
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
