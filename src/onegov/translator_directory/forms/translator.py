from wtforms import SelectField, StringField, BooleanField, TextAreaField
from wtforms.fields.html5 import DateField, EmailField, IntegerField
from wtforms.validators import InputRequired, Email, Optional

from onegov.form import Form
from onegov.form.fields import ChosenSelectField

from onegov.form.validators import ValidPhoneNumber
from onegov.translator_directory import _
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import order_cols
from onegov.translator_directory.models.translator import GENDERS


class LanguageFormMixin:

    @property
    def available_languages(self):
        return LanguageCollection(self.request.session).query()


class TranslatorForm(Form):

    """
    Todo:
    - validate unique email
    - ....
    """

    first_name = StringField(
        label=_('First name'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    last_name = StringField(
        label=_('Last name'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    pers_id = IntegerField(
        label=_('Personal ID')
    )

    address = StringField(
        label=_('Address'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    zip_code = StringField(
        label=_('Zip Code'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    city = StringField(
        label=_('City'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    gender = SelectField(
        label=_('Gender'),
        validators=[InputRequired()],
        fieldset=_('Personal Information'),
        choices=[
            (g, g) for g in GENDERS
        ]
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    nationality = StringField(
        label=_('Nationality'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    withholding_tax = StringField(
        label=_('Withholding tax'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    email = EmailField(
        label=_('Email'),
        validators=[Optional(), Email()],
        fieldset=_('Contact Information')
    )

    tel_mobile = StringField(
        label=_('Mobile Number'),
        validators=[InputRequired(), ValidPhoneNumber()],
        fieldset=_('Contact Information')
    )

    tel_private = StringField(
        label=_('Private Phone Number'),
        validators=[Optional(), ValidPhoneNumber()],
        fieldset=_('Contact Information')
    )

    tel_office = StringField(
        label=_('Office Phone Number'),
        validators=[Optional(), ValidPhoneNumber()],
        fieldset=_('Contact Information')
    )

    availability = StringField(
        label=_('Availability'),
        fieldset=_('Contact Information')
    )

    # Todo: Add description field
    confirm_name_reveal = BooleanField(
        label=_('Name revealing confirmation'),
    )

    mother_tongue = SelectField(
        label=_('Mother tongue'),
        validators=[InputRequired()],
        fieldset=_('Languages skills')
    )

    spoken_languages = ChosenSelectField(
        label=_('Spoken languages'),
        validators=[InputRequired()],
        fieldset=_('Languages skills')
    )

    written_languages = ChosenSelectField(
        label=_('Written languages'),
        validators=[InputRequired()],
        fieldset=_('Languages skills')
    )

    # certificates, multi file upload field

    # applications

    comments = TextAreaField(
        label=_('Comments')
    )


class TranslatorSearchForm(Form, LanguageFormMixin):

    spoken_languages = ChosenSelectField(
        label=_('Spoken languages')
    )

    written_languages = ChosenSelectField(
        label=_('Written languages')
    )

    order_by = SelectField(
        label=_('Order by'),
        choices=[
            (order_cols[0], _('Last name')),
            (order_cols[1], _('Driving distance'))
        ]
    )

    def on_request(self):
        lang_choices = [
            (la, la) for la in self.available_languages
        ]
        self.spoken_languages.choices = lang_choices
        self.written_languages.choices = lang_choices
