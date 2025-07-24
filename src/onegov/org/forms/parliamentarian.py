from __future__ import annotations

from onegov.form.fields import PhoneNumberField
from onegov.form.fields import TranslatedSelectField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import ValidPhoneNumber
from onegov.org import _
from onegov.parliament.models.parliamentarian import GENDERS
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL


class ParliamentarianForm(NamedFileForm):

    gender = TranslatedSelectField(
        label=_('Gender'),
        fieldset=_('Basic properties'),
        choices=list(GENDERS.items()),
        validators=[InputRequired()],
        default='male'
    )

    first_name = StringField(
        label=_('First name'),
        fieldset=_('Basic properties'),
        validators=[InputRequired()],
    )

    last_name = StringField(
        label=_('Last name'),
        fieldset=_('Basic properties'),
        validators=[InputRequired()],
    )

    picture = UploadField(
        label=_('Picture'),
        fieldset=_('Basic properties'),
    )

    private_address = StringField(
        label=_('Address'),
        fieldset=_('Private address'),
    )

    private_address_addition = StringField(
        label=_('Addition'),
        fieldset=_('Private address'),
    )

    private_address_zip_code = StringField(
        label=_('Zip code'),
        fieldset=_('Private address'),
    )

    private_address_city = StringField(
        label=_('City'),
        fieldset=_('Private address'),
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_('Additional information'),
        validators=[Optional()],
    )

    # just commented as not used but still as column in the database
    # date_of_death = DateField(
    #     label=_('Date of death'),
    #     fieldset=_('Additional information'),
    #     validators=[Optional()],
    # )

    place_of_origin = StringField(
        label=_('Place of origin'),
        fieldset=_('Additional information'),
    )

    occupation = StringField(
        label=_('Occupation'),
        fieldset=_('Additional information'),
    )

    academic_title = StringField(
        label=_('Academic title'),
        fieldset=_('Additional information'),
    )

    salutation = StringField(
        label=_('Salutation'),
        fieldset=_('Additional information'),
    )

    phone_private = PhoneNumberField(
        label=_('Private phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    phone_mobile = PhoneNumberField(
        label=_('Mobile phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    phone_business = PhoneNumberField(
        label=_('Business phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    email_primary = EmailField(
        label=_('Primary email address'),
        fieldset=_('Additional information'),
        validators=[InputRequired(), Email()]
    )

    email_secondary = EmailField(
        label=_('Secondary email address'),
        fieldset=_('Additional information'),
        validators=[Optional(), Email()]
    )

    website = URLField(
        label=_('Website'),
        fieldset=_('Additional information'),
        validators=[URL(), Optional()]
    )

    remarks = TextAreaField(
        label=_('Remarks'),
        fieldset=_('Additional information'),
    )
