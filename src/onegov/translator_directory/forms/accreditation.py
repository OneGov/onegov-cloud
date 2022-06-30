from datetime import date
from cached_property import cached_property
from onegov.core.crypto import random_token
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import TagsField
from onegov.form.fields import UploadField
from wtforms.validators import DataRequired
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import Stdnum
from onegov.form.validators import StrictOptional
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import CoordinatesField
from onegov.translator_directory import _
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.forms.mixins import DrivingDistanceMixin
from onegov.translator_directory.models.translator import Translator
from re import match
from wtforms import BooleanField
from wtforms import FloatField
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


class RequestAccreditationForm(Form, DrivingDistanceMixin):

    callout = _(
        'Make sure you have all information and scans of the required '
        'documents before starting to fill out the form!'
    )

    last_name = StringField(
        label=_('Last name'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    first_name = StringField(
        label=_('First name'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    gender = ChosenSelectField(
        label=_('Gender'),
        fieldset=_('Personal Information'),
        choices=list(GENDERS.items()),
        validators=[InputRequired()],
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    hometown = StringField(
        label=_('Hometown'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    nationality = StringField(
        label=_('Nationality'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    marital_status = StringField(
        label=_('Marital status'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    coordinates = CoordinatesField(
        label=_('Location'),
        description=_(
            'Search for the exact address to set a marker. The address fields '
            'beneath are filled out automatically.'
        ),
        fieldset=_('Personal Information'),
        render_kw={'data-map-type': 'marker'},
        validators=[InputRequired()],
    )

    address = StringField(
        label=_('Street and house number'),
        fieldset=_('Personal Information'),
        render_kw={'readonly': True},
        validators=[InputRequired()],
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_('Personal Information'),
        render_kw={'readonly': True},
        validators=[InputRequired()],
    )

    city = StringField(
        label=_('City'),
        fieldset=_('Personal Information'),
        render_kw={'readonly': True},
        validators=[InputRequired()],
    )

    # todo: hide?
    drive_distance = FloatField(
        label=_('Drive distance (km)'),
        fieldset=_('Personal Information'),
        validators=[Optional()],
        render_kw={'readonly': True},
    )

    withholding_tax = BooleanField(
        label=_('Withholding tax'),
        fieldset=_('Personal Information'),
        default=False
    )

    self_employed = BooleanField(
        label=_('Self-employed'),
        fieldset=_('Personal Information'),
        default=False
    )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[ValidSwissSocialSecurityNumber()],
        fieldset=_('Identification / Bank details'),
    )

    bank_name = StringField(
        label=_('Bank name'),
        fieldset=_('Identification / Bank details'),
        validators=[InputRequired()],
    )

    bank_address = StringField(
        label=_('Bank address'),
        fieldset=_('Identification / Bank details'),
        validators=[InputRequired()],
    )

    iban = StringField(
        label=_('IBAN'),
        fieldset=_('Identification / Bank details'),
        validators=[Stdnum(format='iban'), InputRequired()],
    )

    account_owner = StringField(
        label=_('Account owner'),
        fieldset=_('Identification / Bank details'),
        validators=[InputRequired()],
    )

    contact_hint = PanelField(
        text=_(
            'Attention: It must be ensured that no one other than the '
            'applicant can take note of the information transmitted with '
            'the following contact details!'
        ),
        kind='callout',
        fieldset=_('Contact')
    )

    email = EmailField(
        label=_('Email'),
        validators=[InputRequired(), Email()],
        fieldset=_('Contact')
    )

    tel_private = StringField(
        label=_('Private Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_('Contact'),
    )

    tel_office = StringField(
        label=_('Office Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_('Contact'),
    )

    tel_mobile = StringField(
        label=_('Mobile Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_('Contact'),
    )

    availability = SelectField(
        label=_('Availability'),
        fieldset=_('Contact'),
        choices=[
            ('24h', '24h'),
            ('Vereinbarung', 'Vereinbarung')
        ],
        validators=[InputRequired()],
    )

    availability_has_restriction = BooleanField(
        label=_('Restriction regarding availability'),
        fieldset=_('Contact'),
        default=False
    )

    availability_restriction = StringField(
        label=_('Restriction'),
        fieldset=_('Contact'),
        depends_on=('availability_has_restriction', 'y'),
    )

    confirm_name_reveal = BooleanField(
        label=_(
            'Do you agree to the disclosure of your name to other persons '
            'and authorities within and outside the Canton of Zug?'
        ),
        fieldset=_('Legal')
    )

    learned_profession = StringField(
        label=_('Learned profession'),
        fieldset=_('Training'),
        validators=[InputRequired()],
    )

    current_profession = StringField(
        label=_('Current professional activity'),
        fieldset=_('Training'),
        validators=[InputRequired()],
    )

    education_as_interpreter = BooleanField(
        label=_('Interpreter education with degree'),
        fieldset=_('Training'),
    )

    languages_hint_1 = PanelField(
        text=_(
            'I apply for accreditation for the following working languages.'
        ),
        kind='',
        fieldset=_('Language training - Expertise')
    )

    languages_hint_2 = PanelField(
        text=_('German C2 is a prerequisite.'),
        kind='callout',
        fieldset=_('Language training - Expertise')
    )

    mother_tongues_ids = ChosenSelectMultipleField(
        label=_('Mother tongues'),
        fieldset=_('Language training - Expertise'),
        validators=[InputRequired()],
        choices=[],
    )

    spoken_languages_ids = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        description=_('Mention only languages with level C2.'),
        fieldset=_('Language training - Expertise'),
        validators=[StrictOptional()],
        choices=[]
    )

    written_languages_ids = ChosenSelectMultipleField(
        label=_('Written languages'),
        description=_('Mention only languages with level C2.'),
        fieldset=_('Language training - Expertise'),
        validators=[StrictOptional()],
        choices=[]
    )

    expertise_professional_guilds = ChosenSelectMultipleField(
        label=_('Expertise by professional guild'),
        fieldset=_('Qualifications'),
        choices=[]
    )

    expertise_professional_guilds_other = TagsField(
        label=_('Expertise by professional guild: other'),
        description=_('Comma-separated listing'),
        fieldset=_('Qualifications')
    )

    expertise_interpreting_types = ChosenSelectMultipleField(
        label=_('Expertise by interpreting type'),
        fieldset=_('Qualifications'),
        choices=[]
    )

    agency_references = StringField(
        label=_('Authorities and courts'),
        fieldset=_('References'),
    )

    admission = BooleanField(
        label=_(
            'Admission course of the high court of the Canton of Zurich '
            'available'
        ),
        fieldset=_('Admission course'),
        default=False
    )

    admission_course_agreement = BooleanField(
        label=_(
            "I agree to attend the admission course of the high court of the "
            "Canton of Zürich at my own expense CHF 1'100.00."
        ),
        fieldset=_('Admission course'),
        default=False,
        depends_on=('admission', '!y'),
    )

    admission_hint = PanelField(
        text=_(
            'If a German C2 certificate is required, an additional CHF '
            '100.00 will be charged. The admission course is a basic '
            'requirement for an application. Administration is carried out by '
            'the Translation Coordination Office of the Zug authorities and '
            'courts.'
        ),
        kind='',
        fieldset=_('Admission course'),
        depends_on=('admission', '!y'),
    )

    documents_hint = PanelField(
        text=_(
            'In order for your application for inclusion in the directory to '
            'be processed, a complete application must be submitted. '
            'This includes the following documents:'
        ),
        kind='',
        fieldset=_('Documents')
    )

    # todo: Hint where to download
    declaration_of_authorization = UploadField(
        label=_('Signed declaration of authorization (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    letter_of_motivation = UploadField(
        label=_('Short letter of motivation (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    resume = UploadField(
        label=_('Resume (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    certificates = UploadField(
        label=_('Certificates (PDF)'),
        description=_(
            'For the last five years. Language proficiency certificates '
            'level C2 are mandatory for non-native speakers.'
        ),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    social_security_card = UploadField(
        label=_('Social security card (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    passport = UploadField(
        label=_('Identity card, passport or foreigner identity card (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    passport_photo = UploadField(
        label=_('Current passport photo (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    debt_collection_register_extract = UploadField(
        label=_('Current extract from the debt collection register (PDF)'),
        description=_('Maximum 6 months since issue.'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    criminal_register_extract = UploadField(
        label=_('Current extract from the Central Criminal Register (PDF)'),
        description=_(
            'Maximum 6 months since issue. Online order at '
            'www.strafregister.admin.ch'
        ),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    certificate_of_capability = UploadField(
        label=_('Certificate of Capability (PDF)'),
        description=_('Available from the municipal or city administration.'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw=dict(force_simple=True),
        fieldset=_('Documents')
    )

    submission_hint = PanelField(
        text=_('Your data will be treated with strict confidentiality.'),
        kind='',
        render_kw=dict(force_simple=True),
        fieldset=_('Submission')
    )

    remarks = TextAreaField(
        label=_('Remarks'),
        render_kw=dict(force_simple=True),
        fieldset=_('Submission')
    )

    confirm_submission = BooleanField(
        label=_('By submitting, I confirm the correctness of the above data.'),
        fieldset=_('Submission'),
        default=False
    )

    def validate_zip_code(self, field):
        if field.data and not match(r'\d{4}', field.data):
            raise ValidationError(_('Zip code must consist of 4 digits'))

    def validate_email(self, field):
        if field.data:
            field.data = field.data.lower()
        query = self.request.session.query
        translator = query(Translator).filter_by(email=field.data).first()
        if translator:
            raise ValidationError(
                _('A translator with this email already exists')
            )

    def validate_confirm_submission(self, field):
        if not field.data:
            raise ValidationError(
                _('Please confirm the correctness of the above data.')
            )

    # todo: ensure at least on phone number?

    @cached_property
    def gender_choices(self):
        return tuple(
            (id_, self.request.translate(choice))
            for id_, choice in GENDERS.items()
        )

    @cached_property
    def language_choices(self):
        languages = LanguageCollection(self.request.session)
        return [
            (str(language.id), language.name)
            for language in languages.query()
        ]

    @cached_property
    def expertise_professional_guilds_choices(self):
        return tuple(
            (id_, self.request.translate(choice))
            for id_, choice in PROFESSIONAL_GUILDS.items()
        )

    @cached_property
    def expertise_interpreting_types_choices(self):
        return tuple(
            (id_, self.request.translate(choice))
            for id_, choice in INTERPRETING_TYPES.items()
        )

    @property
    def mother_tongues(self):
        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.mother_tongues_ids.data)

    @property
    def spoken_languages(self):
        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.spoken_languages_ids.data)

    @property
    def written_languages(self):
        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.written_languages_ids.data)

    def on_request(self):
        self.request.include('tags-input')
        self.gender.choices = self.gender_choices
        self.mother_tongues_ids.choices = self.language_choices
        self.spoken_languages_ids.choices = self.language_choices
        self.written_languages_ids.choices = self.language_choices
        self.expertise_professional_guilds.choices = \
            self.expertise_professional_guilds_choices
        self.expertise_interpreting_types.choices = \
            self.expertise_interpreting_types_choices

    def get_translator_data(self):
        data = self.get_useful_data()
        result = {
            key: data.get(key) for key in (
                'last_name',
                'first_name',
                'gender',
                'date_of_birth',
                'nationality',
                'coordinates',
                'address',
                'zip_code',
                'city',
                'drive_distance',
                'withholding_tax',
                'self_employed',
                'social_sec_number',
                'bank_name',
                'bank_address',
                'iban',
                'account_owner',
                'email',
                'tel_private',
                'tel_office',
                'tel_mobile',
                'availability',
                'confirm_name_reveal',
                'education_as_interpreter',
                'expertise_professional_guilds',
                'expertise_professional_guilds_other',
                'expertise_interpreting_types',
                'agency_references',
            )
        }
        result['mother_tongues'] = self.mother_tongues
        result['spoken_languages'] = self.spoken_languages
        result['written_languages'] = self.written_languages
        result['date_of_application'] = date.today()
        result['admission'] = 'certificed' if data.get('admission') else \
            'uncertified'

        return result

    def get_files(self):

        def as_file(field, category):
            name = self.request.translate(field.label.text)
            name = name.replace(' (PDF)', '')
            return File(
                id=random_token(),
                name=f'{name}.pdf',
                note=category,
                reference=as_fileintent(
                    content=field.file,
                    filename=field.filename
                )
            )

        return [
            as_file(self.declaration_of_authorization, 'Antrag'),
            as_file(self.letter_of_motivation, 'Antrag'),
            as_file(self.resume, 'Antrag'),
            as_file(self.certificates, 'Diplome und Zertifikate'),
            as_file(self.social_security_card, 'Antrag'),
            as_file(self.passport, 'Antrag'),
            as_file(self.passport_photo, 'Antrag'),
            as_file(self.debt_collection_register_extract, 'Antrag'),
            as_file(self.criminal_register_extract, 'Antrag'),
            as_file(self.certificate_of_capability, 'Antrag'),
        ]

    def get_ticket_data(self):
        data = self.get_useful_data()
        return {
            key: data.get(key) for key in (
                'hometown',
                'marital_status',
                'availability_has_restriction',
                'availability_restriction',
                'learned_profession',
                'current_profession',
                'admission_course_agreement',
                'remarks',
            )
        }


class GrantAccreditationForm(Form):

    callout = _('Create a user account and publish the translator.')

    # todo: admission type?
    # todo: certificates


class RefuseAccreditationForm(Form):

    callout = _('Delete all related data.')
