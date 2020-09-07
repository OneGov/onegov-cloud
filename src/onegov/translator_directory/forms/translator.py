import re

from cached_property import cached_property
from wtforms import SelectField, StringField, BooleanField, TextAreaField, \
    RadioField, FloatField
from wtforms.fields.html5 import DateField, EmailField, IntegerField
from wtforms.validators import InputRequired, Email, Optional, ValidationError

from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField

from onegov.form.validators import ValidPhoneNumber, \
    ValidSwissSocialSecurityNumber, StrictOptional
from onegov.translator_directory import _
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import order_cols
from onegov.translator_directory.models.translator import GENDERS, \
    GENDERS_DESC, Translator, mother_tongue_association_table, \
    spoken_association_table, written_association_table, \
    certificate_association_table, ADMISSIONS, ADMISSIONS_DESC


class FormChoicesMixin:

    @property
    def available_languages(self):
        return LanguageCollection(self.request.session).query()

    @property
    def available_certificates(self):
        return LanguageCertificateCollection(self.request.session).query()

    @cached_property
    def language_choices(self):
        return tuple(
            (str(lang.id), lang.name) for lang in self.available_languages
        )

    @cached_property
    def certificate_choices(self):
        return tuple(
            (str(cert.id), cert.name) for cert in self.available_certificates
        )

    @cached_property
    def gender_choices(self):
        return tuple(
            (id_, self.request.translate(choice))
            for id_, choice in zip(GENDERS, GENDERS_DESC)
        )

    @staticmethod
    def associated_ids(model, attr):
        return [
            str(item.id) for item in getattr(model, attr)
        ]


class TranslatorForm(Form, FormChoicesMixin):

    pers_id = IntegerField(
        label=_('Personal ID'),
        validators=[Optional()]
    )

    admission = RadioField(
        label=_('Admission'),
        choices=tuple(
            (id_, label) for id_, label in zip(ADMISSIONS, ADMISSIONS_DESC)
        ),
        default=ADMISSIONS[0]
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

    drive_distance = FloatField(
        label=_('Drive distance'),
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

    mother_tongues = ChosenSelectMultipleField(
        label=_('Mother tongue'),
        validators=[InputRequired()],
        choices=[]
    )

    spoken_languages = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    written_languages = ChosenSelectMultipleField(
        label=_('Written languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    proof_of_preconditions = StringField(
        label=_('Proof of preconditions')
    )

    agency_references = TextAreaField(
        label=_('Agency references'),
        validators=[InputRequired()],
        render_kw={'rows': 3}
    )

    education_as_interpreter = BooleanField(
        label=_('Education as interpreter'),
        default=False
    )

    # certificates
    certificates = ChosenSelectMultipleField(
        label=_('Language Certificates'),
        validators=[Optional()],
        choices=[]
    )

    comments = TextAreaField(
        label=_('Comments')
    )

    hide = BooleanField(
        label=_('Hidden'),
        default=False
    )

    # Here come the actual file fields to upload stuff

    def on_request(self):
        self.gender.choices = self.gender_choices
        self.mother_tongues.choices = self.language_choices
        self.spoken_languages.choices = self.language_choices
        self.written_languages.choices = self.language_choices
        self.certificates.choices = self.certificate_choices

    def get_useful_data(self, exclude={'csrf_token'}):
        data = super().get_useful_data(
            exclude={'csrf_token', 'spoken_languages', 'written_languages',
                     'certificates', 'mother_tongues'})

        languages = LanguageCollection(self.request.session)

        if self.mother_tongues.data:
            langs = languages.by_ids(self.mother_tongues.data).all()
            assert len(langs) == len(self.mother_tongues.data)
            data['mother_tongues'] = langs

        if self.spoken_languages.data:
            spoken = languages.by_ids(self.spoken_languages.data).all()
            assert len(spoken) == len(self.spoken_languages.data)
            data['spoken_languages'] = spoken

        if self.written_languages.data:
            written = languages.by_ids(self.written_languages.data).all()
            assert len(written) == len(self.written_languages.data)
            data['written_languages'] = written

        lang_certs = LanguageCertificateCollection(self.request.session)
        if self.certificates.data:
            certs = lang_certs.by_ids(self.certificates.data).all()
            assert len(certs) == len(self.certificates.data)
            data['certificates'] = certs

        return data

    def validate_zip_code(self, field):
        if field.data and not re.match(r'\d{4}', field.data):
            raise ValidationError(_('Zip code must consist of 4 digits'))

    def validate_email(self, field):
        if field.data:
            field.data = field.data.lower()
            trs = self.request.session.query(Translator).filter_by(
                    email=field.data).first()
            if trs and getattr(self.model, 'id', trs.id) != trs.id:
                raise ValidationError(
                    _("A translator with this email already exists"))

    def apply_model(self, model):
        # {k: v for k, v in self.data.items() if k not in exclude}
        associated_items = {
            'spoken_languages', 'written_languages', 'mother_tongues',
            'certificates'
        }
        for attr in (field for field in self._fields if field != 'csrf_token'):
            getattr(self, attr).data = getattr(model, attr)
        for attr in associated_items:
            getattr(self, attr).data = self.associated_ids(model, attr)


class TranslatorSearchForm(Form, FormChoicesMixin):

    spoken_langs = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        choices=[]
    )

    written_langs = ChosenSelectMultipleField(
        label=_('Written languages'),
        choices=[]
    )

    order_by = RadioField(
        label=_('Order by'),
        choices=(
            (order_cols[0], _('Last name')),
            (order_cols[1], _('Drive distance')),
        ),
        default=order_cols[0]
    )

    order_desc = RadioField(
        label=_("Order direction"),
        choices=(
            ('0', _("Ascending")),
            ('1', _("Descending"))
        ),
        default='0'
    )

    def apply_model(self, model):

        if model.spoken_langs:
            self.spoken_langs.data = model.spoken_langs

        if model.written_langs:
            self.written_langs.data = model.written_langs
        self.order_by.data = model.order_by
        self.order_desc.data = model.order_desc and '1' or '0'

    def update_model(self, model):
        model.spoken_langs = self.spoken_langs.data
        model.written_langs = self.written_langs.data
        model.order_by = self.order_by.data
        model.order_desc = self.order_desc == '1' and True or False

    def on_request(self):
        self.spoken_langs.choices = self.language_choices
        self.written_langs.choices = self.language_choices
