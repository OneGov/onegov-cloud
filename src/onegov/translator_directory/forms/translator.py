from cached_property import cached_property
from wtforms import SelectField, StringField, BooleanField, TextAreaField
from wtforms.fields.html5 import DateField, EmailField, IntegerField
from wtforms.validators import InputRequired, Email, Optional, ValidationError

from onegov.form import Form
from onegov.form.fields import ChosenSelectField

from onegov.form.validators import ValidPhoneNumber, \
    ValidSwissSocialSecurityNumber, StrictOptional
from onegov.translator_directory import _
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import order_cols
from onegov.translator_directory.models.translator import GENDERS, \
    GENDERS_DESC, CERTIFICATES, Translator


class LanguageFormMixin:

    @property
    def available_languages(self):
        return LanguageCollection(self.request.session).query()

    @cached_property
    def language_choices(self):
        return tuple(
            (str(lang.id), lang.name) for lang in self.available_languages
        )


class TranslatorForm(Form, LanguageFormMixin):

    pers_id = IntegerField(
        label=_('Personal ID'),
        validators=[Optional()]
    )

    first_name = StringField(
        label=_('First name'),
        validators=[InputRequired()],
    )

    last_name = StringField(
        label=_('Last name'),
        validators=[InputRequired()]
    )

    gender = SelectField(
        label=_('Gender'),
        validators=[StrictOptional()],
        choices=[]
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_('Personal Information'),
        validators=[Optional()]
    )

    nationality = StringField(
        label=_('Nationality'),
        validators=[Optional()]
    )

    address = StringField(
        label=_('Address'),
    )

    zip_code = StringField(
        label=_('Zip Code'),
    )

    city = StringField(
        label=_('City'),
    )

    drive_distance = IntegerField(
        label=_('Driving Distance'),
        validators=[Optional()]
    )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[Optional(), ValidSwissSocialSecurityNumber()],
    )

    bank_name = StringField(
        label=_('Bank name')
    )

    bank_address = StringField(
        label=_('Bank address')
    )

    account_owner = StringField(
        label=_('Account owner')
    )

    email = EmailField(
        label=_('Email'),
        validators=[Optional(), Email()],
    )

    withholding_tax = StringField(
        label=_('Withholding tax'),
    )

    tel_mobile = StringField(
        label=_('Mobile Number'),
        validators=[Optional(), ValidPhoneNumber()],
    )

    tel_private = StringField(
        label=_('Private Phone Number'),
        validators=[Optional(), ValidPhoneNumber()],
    )

    tel_office = StringField(
        label=_('Office Phone Number'),
        validators=[Optional(), ValidPhoneNumber()],
    )

    availability = StringField(
        label=_('Availability'),
    )

    confirm_name_reveal = BooleanField(
        label=_('Name revealing confirmation'),
    )

    date_of_application = DateField(
        label=_('Date of application'),
        validators=[Optional()]
    )

    date_of_decision = DateField(
        label=_('Date of decision'),
        validators=[Optional()]
    )

    mother_tongue_id = SelectField(
        label=_('Mother tongue'),
        validators=[InputRequired()],
        choices=[]
    )

    spoken_languages = ChosenSelectField(
        label=_('Spoken languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    written_languages = ChosenSelectField(
        label=_('Written languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    proof_of_preconditions = StringField(
        label=_('Proof of preconditions')
    )

    agency_references = TextAreaField(
        label=_('Agency references'),
        validators=[InputRequired()]
    )

    education_as_interpreter = BooleanField(
        label=_('Education as interpreter'),
        default=False
    )

    # certificates, multi file upload field
    certificate = SelectField(
        label=_('Certificate'),
        validators=[Optional()],
        choices=tuple((cert, cert) for cert in CERTIFICATES)
    )

    comments = TextAreaField(
        label=_('Comments')
    )

    # Here come the actual file fields to upload stuff

    @cached_property
    def gender_choices(self):
        return tuple(
            (id_, self.request.translate(choice))
            for id_, choice in zip(GENDERS, GENDERS_DESC)
        )

    def on_request(self):
        self.gender.choices = self.gender_choices
        self.mother_tongue_id.choices = self.language_choices
        self.spoken_languages.choices = self.language_choices
        self.written_languages.choices = self.language_choices

    def get_useful_data(self, exclude={'csrf_token'}):
        data = super().get_useful_data(
            exclude={'csrf_token', 'spoken_languages', 'written_languages',
                     'mother_tongue'})
        return data

    def validate_email(self, field):
        if field.data:
            field.data = field.data.lower()
            if self.request.session.query(Translator).filter_by(
                    email=field.data).first():
                raise ValidationError(
                    _("A translator with this email already exists"))


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
        self.spoken_languages.choices = self.language_choices
        self.written_languages.choices = self.language_choices
