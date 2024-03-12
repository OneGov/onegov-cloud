from onegov.form.forms import NamedFileForm
from onegov.pas import _
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class ParliamentarianForm(NamedFileForm):

    personnel_number = StringField(
        label=_('Personnel number'),
        fieldset=_('Basic properties'),
    )

    contract_number = StringField(
        label=_('Contract number'),
        fieldset=_('Basic properties'),
    )

    # todo: gender

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

    # todo: picture_url

    # todo: shipping_method*

    shipping_address = StringField(
        label=_('Address'),
        fieldset=_('Shipping address'),
    )

    shipping_address_addition = StringField(
        label=_('Addition'),
        fieldset=_('Shipping address'),
    )

    shipping_address_zip_code = StringField(
        label=_('Zip code'),
        fieldset=_('Shipping address'),
    )

    shipping_address_city = StringField(
        label=_('City'),
        fieldset=_('Shipping address'),
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

    date_of_death = DateField(
        label=_('Date of death'),
        fieldset=_('Additional information'),
        validators=[Optional()],
    )

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

    salutation_for_address = StringField(
        label=_('Salutation used in the address'),
        fieldset=_('Additional information'),
    )

    salutation_for_letter = StringField(
        label=_('Salutation used for letters'),
        fieldset=_('Additional information'),
    )

    forwarding_of_bills = StringField(
        label=_('How bills should be delivered'),
        fieldset=_('Additional information'),
    )

    # todo: phone number?
    phone_private = StringField(
        label=_('Private phone number'),
        fieldset=_('Additional information'),
    )

    # todo: phone number?
    phone_mobile = StringField(
        label=_('Mobile phone number'),
        fieldset=_('Additional information'),
    )

    # todo: phone number?
    phone_business = StringField(
        label=_('Business phone number'),
        fieldset=_('Additional information'),
    )

    # todo: email?
    email_primary = StringField(
        label=_('Primary email address'),
        fieldset=_('Additional information'),
        validators=[InputRequired()]
    )

    # todo: email?
    email_secondary = StringField(
        label=_('Secondary email address'),
        fieldset=_('Additional information'),
    )

    # todo: url
    website = StringField(
        label=_('Website'),
        fieldset=_('Additional information'),
    )

    remarks = TextAreaField(
        label=_('Remarks'),
        fieldset=_('Additional information'),
    )
