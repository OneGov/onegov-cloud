import re

from cached_property import cached_property
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import TagsField
from onegov.form.validators import Stdnum
from onegov.form.validators import StrictOptional
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.gis import CoordinatesField
from onegov.translator_directory import _
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import order_cols
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import full_text_max_chars
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.forms.mixins import DrivingDistanceMixin
from onegov.translator_directory.models.translator import \
    certificate_association_table
from onegov.translator_directory.models.translator import \
    monitoring_association_table
from onegov.translator_directory.models.translator import \
    mother_tongue_association_table
from onegov.translator_directory.models.translator import \
    spoken_association_table
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.models.translator import \
    written_association_table
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import FloatField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import ValidationError


class FormChoicesMixin:

    @property
    def available_languages(self):
        return LanguageCollection(self.request.session).query()

    @property
    def available_certificates(self):
        return LanguageCertificateCollection(self.request.session).query()

    @property
    def available_additional_guilds(self):
        translators = TranslatorCollection(self.request.app)
        return translators.available_additional_professional_guilds

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
            for id_, choice in GENDERS.items()
        )

    @staticmethod
    def get_ids(model, attr):
        return [
            str(item.id) for item in getattr(model, attr)
        ]

    @cached_property
    def interpret_types_choices(self):
        return tuple(
            (k, self.request.translate(v))
            for k, v in INTERPRETING_TYPES.items()
        )

    @cached_property
    def guilds_choices(self):
        result = [
            (k, self.request.translate(v))
            for k, v in PROFESSIONAL_GUILDS.items()
        ]
        result.extend([(k, k) for k in self.available_additional_guilds])
        return sorted(result, key=lambda x: x[1].upper())

    @cached_property
    def admission_choices(self):
        admissions = tuple(
            (k, self.request.translate(v))
            for k, v in ADMISSIONS.items()
        )
        return sorted(admissions, key=lambda x: x[1].upper())


class EditorTranslatorForm(Form, FormChoicesMixin):

    pers_id = IntegerField(
        label=_('Personal ID'),
        validators=[Optional()]
    )

    def update_model(self, model):
        model.pers_id = self.pers_id.data or None


class TranslatorForm(Form, FormChoicesMixin, DrivingDistanceMixin):

    pers_id = IntegerField(
        label=_('Personal ID'),
        validators=[Optional()]
    )

    admission = RadioField(
        label=_('Admission'),
        choices=tuple(
            (id_, label) for id_, label in ADMISSIONS.items()
        ),
        default=list(ADMISSIONS)[0]
    )

    withholding_tax = BooleanField(
        label=_('Withholding tax'),
        default=False
    )

    self_employed = BooleanField(
        label=_('Self-employed'),
        default=False
    )

    last_name = StringField(
        label=_('Last name'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    first_name = StringField(
        label=_('First name'),
        validators=[InputRequired()],
        fieldset=_('Personal Information')
    )

    gender = SelectField(
        label=_('Gender'),
        validators=[StrictOptional()],
        choices=[],
        fieldset=_('Personal Information')
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        validators=[Optional()],
        fieldset=_('Personal Information')
    )

    nationality = StringField(
        label=_('Nationality'),
        validators=[Optional()],
        fieldset=_('Personal Information')
    )

    coordinates = CoordinatesField(
        label=_("Location"),
        description=_(
            "Search for the exact address to set a marker. The address fields "
            "beneath are filled out automatically."
        ),
        fieldset=_("Address"),
        render_kw={'data-map-type': 'marker'}
    )

    address = StringField(
        label=_('Street and house number'),
        fieldset=_('Address')
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_('Address')
    )

    city = StringField(
        label=_('City'),
        fieldset=_('Address')
    )

    drive_distance = FloatField(
        label=_('Drive distance (km)'),
        validators=[Optional()],
        fieldset=_('Address'),
    )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[Optional(), ValidSwissSocialSecurityNumber()],
        fieldset=_('Identification / bank account')
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

    iban = StringField(
        label=_('IBAN'),
        validators=[Optional(), Stdnum(format='iban')]
    )

    email = EmailField(
        label=_('Email'),
        validators=[Optional(), Email()],
        fieldset=_('Contact information')
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

    operation_comments = TextAreaField(
        label=_('Comments on possible field of application'),
        render_kw={'rows': 3}
    )

    confirm_name_reveal = BooleanField(
        label=_('Name revealing confirmation'),
        fieldset=_('Legal information'),
        description=_('Consent to the disclosure of the name '
                      'to other persons and authorities')
    )

    date_of_application = DateField(
        label=_('Date of application'),
        validators=[Optional()],
        fieldset=_('Admission to the directory')
    )

    date_of_decision = DateField(
        label=_('Date of decision'),
        validators=[Optional()],
    )

    mother_tongues_ids = ChosenSelectMultipleField(
        label=_('Mother tongues'),
        validators=[InputRequired()],
        choices=[],
        fieldset=_('Language training and expertise')
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

    monitoring_languages_ids = ChosenSelectMultipleField(
        label=_('Monitoring languages'),
        validators=[StrictOptional()],
        choices=[]
    )

    profession = StringField(
        label=_('Learned profession')
    )

    occupation = StringField(
        label=_('Current professional activity')
    )

    expertise_professional_guilds = MultiCheckboxField(
        label=_('Expertise by professional guild'),
        choices=[
            (id_, label) for id_, label in PROFESSIONAL_GUILDS.items()
        ]
    )

    expertise_professional_guilds_other = TagsField(
        label=_('Expertise by professional guild: other')
    )

    expertise_interpreting_types = MultiCheckboxField(
        label=_('Expertise by interpreting type'),
        choices=[
            (id_, label) for id_, label in INTERPRETING_TYPES.items()
        ]
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
        return LanguageCertificateCollection(self.request.session)

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

    @property
    def monitoring_languages(self):
        return self.lang_collection.by_ids(self.monitoring_languages_ids.data)

    special_fields = {
        'mother_tongues_ids': mother_tongue_association_table,
        'spoken_languages_ids': spoken_association_table,
        'written_languages_ids': written_association_table,
        'monitoring_languages_ids': monitoring_association_table,
        'certificates_ids': certificate_association_table
    }

    # Here come the actual file fields to upload stuff

    def on_request(self):
        self.request.include('tags-input')
        self.gender.choices = self.gender_choices
        self.mother_tongues_ids.choices = self.language_choices
        self.spoken_languages_ids.choices = self.language_choices
        self.written_languages_ids.choices = self.language_choices
        self.monitoring_languages_ids.choices = self.language_choices
        self.certificates_ids.choices = self.certificate_choices
        self.hide(self.drive_distance)

    def get_useful_data(self):
        """Do not use to update and instance of a translator."""
        data = super().get_useful_data(
            exclude={'csrf_token', *self.special_fields.keys()}
        )

        data['email'] = data['email'] or None
        data['mother_tongues'] = self.mother_tongues
        data['spoken_languages'] = self.spoken_languages
        data['written_languages'] = self.written_languages
        data['monitoring_languages'] = self.monitoring_languages
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
        translators = TranslatorCollection(self.request.app)
        translators.update_user(model, self.email.data)

        model.first_name = self.first_name.data
        model.last_name = self.last_name.data
        model.iban = self.iban.data
        model.pers_id = self.pers_id.data or None
        model.admission = self.admission.data
        model.withholding_tax = self.withholding_tax.data
        model.self_employed = self.self_employed.data
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
        model.profession = self.profession.data
        model.occupation = self.occupation.data
        model.operation_comments = self.operation_comments.data or None
        model.coordinates = self.coordinates.data

        self.update_association(model, 'mother_tongues', '_ids')
        self.update_association(model, 'spoken_languages', '_ids')
        self.update_association(model, 'written_languages', '_ids')
        self.update_association(model, 'monitoring_languages', '_ids')
        self.update_association(model, 'certificates', '_ids')

        model.expertise_professional_guilds = \
            self.expertise_professional_guilds.data
        model.expertise_professional_guilds_other = \
            self.expertise_professional_guilds_other.data
        model.expertise_interpreting_types = \
            self.expertise_interpreting_types.data


class TranslatorSearchForm(Form, FormChoicesMixin):

    spoken_langs = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        choices=[]
    )

    written_langs = ChosenSelectMultipleField(
        label=_('Written languages'),
        choices=[]
    )

    interpret_types = ChosenSelectMultipleField(
        label=_('Expertise by interpreting type'),
        choices=[]
    )

    guilds = ChosenSelectMultipleField(
        label=_('Expertise by professional guild'),
        choices=[]
    )

    admission = ChosenSelectMultipleField(
        label=_('Admission'),
        choices=[]
    )

    gender = RadioField(
        label=_('Gender'),
        choices=[],
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

    search = StringField(
        label=_('Search in first and last name'),
        validators=[Optional(), Length(max=full_text_max_chars)]
    )

    def apply_model(self, model):

        if model.spoken_langs:
            self.spoken_langs.data = model.spoken_langs

        if model.gender:
            self.gender.data = model.gender

        if model.written_langs:
            self.written_langs.data = model.written_langs
        self.order_by.data = model.order_by
        self.order_desc.data = model.order_desc and '1' or '0'
        self.search.data = model.search
        self.interpret_types.data = model.interpret_types or []
        self.guilds.data = model.guilds or []
        self.admission.data = model.admissions or []

    def update_model(self, model):
        model.spoken_langs = self.spoken_langs.data
        model.written_langs = self.written_langs.data
        model.order_by = self.order_by.data
        model.order_desc = self.order_desc.data == '1' and True or False
        model.search = self.search.data
        model.interpret_types = self.interpret_types.data
        model.guilds = self.guilds.data
        model.admissions = self.admission.data
        model.gender = self.gender.data

    def on_request(self):
        self.spoken_langs.choices = self.language_choices
        self.written_langs.choices = self.language_choices
        self.guilds.choices = self.guilds_choices
        self.interpret_types.choices = self.interpret_types_choices
        self.admission.choices = self.admission_choices
        self.gender.choices = self.gender_choices
