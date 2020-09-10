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
from onegov.gis import CoordinatesField
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
    def get_ids(model, attr):
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

    # Todo: Activating this field will result in an error when setting the
    # value in the CoordinatesMixin: self.content is None, while it should be
    # a field that is not nullable
    # coordinates = CoordinatesField(
    #     label=_("Coordinates"),
    #     description=_("The marker can be moved by dragging it with the mouse"),
    #     render_kw={'data-map-type': 'marker'}
    # )

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

    mother_tongues_ids = ChosenSelectMultipleField(
        label=_('Mother tongues'),
        validators=[InputRequired()],
        choices=[]
    )

    spoken_languages_ids = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    written_languages_ids = ChosenSelectMultipleField(
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

    certificates_ids = ChosenSelectMultipleField(
        label=_('Language Certificates'),
        validators=[Optional()],
        choices=[]
    )

    comments = TextAreaField(
        label=_('Comments')
    )

    for_admins_only = BooleanField(
        label=_('Hidden'),
        default=False
    )

    @property
    def lang_collection(self):
        return LanguageCollection(self.request.session)

    @property
    def cert_collection(self):
        return LanguageCollection(self.request.session)

    @property
    def certificates(self):
        return self.cert_collection.by_ids(self.certificates_ids.data)

    @property
    def mother_tongues(self):
        return self.lang_collection.by_ids(self.mother_tongues_ids.data)

    @property
    def spoken_languages(self):
        return self.lang_collection.by_ids(self.spoken_languages_ids.data)

    @property
    def written_languages(self):
        return self.lang_collection.by_ids(self.written_languages_ids.data)

    special_fields = {
        'mother_tongues_ids': mother_tongue_association_table,
        'spoken_languages_ids': spoken_association_table,
        'written_languages_ids': written_association_table,
        'certificates_ids': certificate_association_table
    }

    # Here come the actual file fields to upload stuff

    def on_request(self):
        self.gender.choices = self.gender_choices
        self.mother_tongues_ids.choices = self.language_choices
        self.spoken_languages_ids.choices = self.language_choices
        self.written_languages_ids.choices = self.language_choices
        self.certificates_ids.choices = self.certificate_choices

    def get_useful_data(self):
        """Do not use to update and instance of a translator."""
        data = super().get_useful_data(
            exclude={'csrf_token', *self.special_fields.keys()})

        data['mother_tongues'] = self.mother_tongues
        data['spoken_languages'] = self.spoken_languages
        data['written_languages'] = self.written_languages
        data['certificates'] = self.certificates
        return data

    def validate_zip_code(self, field):
        if field.data and not re.match(r'\d{4}', field.data):
            raise ValidationError(_('Zip code must consist of 4 digits'))

    def validate_email(self, field):
        if field.data:
            field.data = field.data.lower()
        if isinstance(self.model, Translator):
            if str(self.model.email) == field.data:
                return
        query = self.request.session.query
        trs = query(Translator).filter_by(email=field.data).first()
        if trs:
            raise ValidationError(
                _("A translator with this email already exists"))

    def update_association(self, model, db_field, suffix):
        field = f'{db_field}{suffix}'
        setattr(model, db_field, [])
        if not getattr(self, field).data:
            return
        for item in getattr(self, db_field):
            getattr(model, db_field).append(item)

    def update_model(self, model):
        """
        We update the model by field explicitely, since using field names with
        setattr or getattr creates new database instance of the model
        """
        model.pers_id = self.pers_id.data or None
        model.admission = self.admission.data
        model.withholding_tax = self.withholding_tax.data or None
        model.gender = self.gender.data
        model.date_of_birth = self.date_of_birth.data or None
        model.nationality = self.nationality.data or None
        model.address = self.address.data or None
        model.zip_code = self.zip_code.data or None
        model.city = self.city.data or None
        model.drive_distance = self.drive_distance.data or None
        model.social_sec_number = self.social_sec_number.data or None
        model.bank_name = self.bank_name.data or None
        model.bank_address = self.bank_address.data or None
        model.account_owner = self.account_owner.data or None
        model.email = self.email.data or None
        model.tel_mobile = self.tel_mobile.data or None
        model.tel_private = self.tel_private.data or None
        model.tel_office = self.tel_office.data or None
        model.availability = self.availability.data or None
        model.confirm_name_reveal = self.confirm_name_reveal.data
        model.date_of_application = self.date_of_application.data or None
        model.date_of_decision = self.date_of_decision.data or None
        model.proof_of_preconditions = self.proof_of_preconditions.data or None
        model.agency_references = self.agency_references.data or None
        model.education_as_interpreter = self.education_as_interpreter.data
        model.comments = self.comments.data or None
        model.for_admins_only = self.for_admins_only.data

        self.update_association(model, 'mother_tongues', '_ids')
        self.update_association(model, 'spoken_languages', '_ids')
        self.update_association(model, 'written_languages', '_ids')
        self.update_association(model, 'certificates', '_ids')


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
