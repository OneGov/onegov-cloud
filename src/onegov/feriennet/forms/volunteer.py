from __future__ import annotations


from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import RadioField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, Email
from onegov.feriennet.utils import decode_name

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.models import VolunteerCart


class VolunteerForm(Form):

    css_class = 'two-columns'

    first_name = StringField(
        label=_('First Name'),
        validators=[InputRequired()])

    last_name = StringField(
        label=_('Last Name'),
        validators=[InputRequired()])

    birth_date = DateField(
        label=_('Birthdate'),
        validators=[InputRequired()])

    organisation = StringField(
        label=_('Organisation'))

    address = TextAreaField(
        label=_('Address'),
        render_kw={'rows': 2},
        validators=[InputRequired()])

    zip_code = StringField(
        label=_('Zip Code'),
        validators=[InputRequired()])

    place = StringField(
        label=_('Place'),
        validators=[InputRequired()])

    email = EmailField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()])

    phone = StringField(
        label=_('Phone'),
        validators=[InputRequired()])

    transport = RadioField(
        label=_('Transport'),
        choices=[
            ('no_pass', _('No pass')),
            ('ga', _('GA')),
            ('half_fare', _('Half Fare Travelcard')),
            ('other_pass', _('Other pass (e.g. zones)')),
            ('own_vehicle', _('Own Vehicle'))
        ],
        default='no_pass',
    )

    note = TextAreaField(
        label=_('Note'),
        render_kw={'rows': 4},
    )

    def process_obj(self, model: VolunteerCart) -> None:  # type:ignore[override]
        current_user = self.request.current_user  # type: ignore

        if current_user:
            self.first_name.data, self.last_name.data = decode_name(
                current_user.realname
            )
            self.email.data = current_user.username
            self.phone.data = current_user.data.get('phone', '')
            self.address.data = current_user.data.get('address', '')
            self.zip_code.data = current_user.data.get('zip_code', '')
            self.place.data = current_user.data.get('place', '')
