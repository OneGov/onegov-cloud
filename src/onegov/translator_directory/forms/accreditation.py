from __future__ import annotations

from datetime import date

from depot.io.utils import FileIntent
from functools import cached_property
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.utils import dictionary_to_binary
from onegov.file import File
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PanelField
from onegov.form.fields import TagsField
from onegov.form.fields import UploadField
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
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import FloatField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING

from onegov.translator_directory.utils import (nationality_choices,
                                               get_custom_text)

if TYPE_CHECKING:
    from onegov.translator_directory.models.language import Language
    from onegov.translator_directory.request import TranslatorAppRequest
    from wtforms.fields.choices import _Choice


class RequestAccreditationForm(Form, DrivingDistanceMixin):

    request: TranslatorAppRequest

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

    nationalities = ChosenSelectMultipleField(
        label=_('Nationality(ies)'),
        fieldset=_('Personal Information'),
        choices=[],  # will be set in on_request
        validators=[InputRequired()],
    )

    marital_status = ChosenSelectField(
        label=_('Marital status'),
        fieldset=_('Personal Information'),
        choices=(
            ('ledig', 'ledig'),
            ('verheiratet', 'verheiratet'),
            ('geschieden', 'geschieden'),
        ),
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
        validators=[InputRequired()],
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    city = StringField(
        label=_('City'),
        fieldset=_('Personal Information'),
        validators=[InputRequired()],
    )

    drive_distance = FloatField(
        label=_('Drive distance (km)'),
        fieldset=_('Personal Information'),
        validators=[Optional()],
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
        validators=[ValidSwissSocialSecurityNumber(), InputRequired()],
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
        validators=[ValidPhoneNumber(), InputRequired()],
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

    confirm_name_reveal = BooleanField(
        label='',  # will be set in on_request
        fieldset=_('Legal')
    )

    profession = StringField(
        label=_('Learned profession'),
        fieldset=_('Training'),
        validators=[InputRequired()],
    )

    occupation = StringField(
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

    monitoring_languages_ids = ChosenSelectMultipleField(
        label=_('Monitoring languages'),
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
        description=('z.B. ZG oder Bund'),
        fieldset=_('References'),
    )

    admission_course_completed = BooleanField(
        label=_(
            'Admission course of the high court of the Canton of Zurich '
            'available'
        ),
        fieldset=_('Admission course'),
        default=False
    )

    admission_course_agreement = BooleanField(
        label='',  # will be set in on_request
        fieldset=_('Admission course'),
        default=False,
        depends_on=('admission_course_completed', '!y'),
    )

    admission_hint = PanelField(
        text='',  # will be set in on_request
        kind='',
        fieldset=_('Admission course'),
        depends_on=('admission_course_completed', '!y'),
    )

    documents_hint = PanelField(
        text='',  # will be set in on_request
        kind='',
        fieldset=_('Documents')
    )

    declaration_of_authorization = UploadField(
        label=_('Signed declaration of authorization (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    letter_of_motivation = UploadField(
        label=_('Short letter of motivation (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    resume = UploadField(
        label=_('Resume (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
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
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    social_security_card = UploadField(
        label=_('Social security card (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    passport = UploadField(
        label=_('Identity card, passport or foreigner identity card (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    passport_photo = UploadField(
        label=_('Current passport photo (PDF)'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
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
        render_kw={'resend_upload': True},
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
        render_kw={'resend_upload': True},
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
        render_kw={'resend_upload': True},
        fieldset=_('Documents')
    )

    confirmation_compensation_office = UploadField(
        label=_(
            'Confirmation from the compensation office regarding '
            'self-employment'
        ),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024),
            DataRequired(),
        ],
        render_kw={'resend_upload': True},
        depends_on=('self_employed', 'y'),
        fieldset=_('Documents')
    )

    submission_hint = PanelField(
        text=_('Your data will be treated with strict confidentiality.'),
        kind='',
        fieldset=_('Submission')
    )

    remarks = TextAreaField(
        label=_('Remarks'),
        fieldset=_('Submission')
    )

    confirm_submission = BooleanField(
        label=_('By submitting, I confirm the correctness of the above data.'),
        fieldset=_('Submission'),
        default=False
    )

    def validate_zip_code(self, field: StringField) -> None:
        if field.data and not match(r'\d{4}', field.data):
            raise ValidationError(_('Zip code must consist of 4 digits'))

    def validate_email(self, field: EmailField) -> None:
        if field.data:
            field.data = field.data.lower()
        query = self.request.session.query
        translator = query(Translator).filter_by(email=field.data)
        if query(translator.exists()).scalar():
            raise ValidationError(
                _('A translator with this email already exists')
            )

    def validate_confirm_submission(self, field: BooleanField) -> None:
        if not field.data:
            raise ValidationError(
                _('Please confirm the correctness of the above data.')
            )

    @cached_property
    def gender_choices(self) -> list[_Choice]:
        return [
            (id_, self.request.translate(choice))
            for id_, choice in GENDERS.items()
        ]

    @cached_property
    def language_choices(self) -> list[_Choice]:
        languages = LanguageCollection(self.request.session)
        return [
            (str(language.id), language.name)
            for language in languages.query()
        ]

    @cached_property
    def expertise_professional_guilds_choices(self) -> list[_Choice]:
        return [
            (id_, self.request.translate(choice))
            for id_, choice in PROFESSIONAL_GUILDS.items()
        ]

    @cached_property
    def expertise_interpreting_types_choices(self) -> list[_Choice]:
        return [
            (id_, self.request.translate(choice))
            for id_, choice in INTERPRETING_TYPES.items()
        ]

    @property
    def mother_tongues(self) -> list[Language]:
        if not self.mother_tongues_ids.data:
            return []

        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.mother_tongues_ids.data)

    @property
    def spoken_languages(self) -> list[Language]:
        if not self.spoken_languages_ids.data:
            return []

        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.spoken_languages_ids.data)

    @property
    def written_languages(self) -> list[Language]:
        if not self.written_languages_ids.data:
            return []

        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.written_languages_ids.data)

    @property
    def monitoring_languages(self) -> list[Language]:
        if not self.monitoring_languages_ids.data:
            return []

        languages = LanguageCollection(self.request.session)
        return languages.by_ids(self.monitoring_languages_ids.data)

    def on_request(self) -> None:
        self.request.include('tags-input')

        self.gender.choices = self.gender_choices
        self.nationalities.choices = nationality_choices(self.request.locale)
        self.mother_tongues_ids.choices = self.language_choices
        self.spoken_languages_ids.choices = self.language_choices
        self.written_languages_ids.choices = self.language_choices
        self.monitoring_languages_ids.choices = self.language_choices
        self.expertise_professional_guilds.choices = (
            self.expertise_professional_guilds_choices)
        self.expertise_interpreting_types.choices = (
            self.expertise_interpreting_types_choices)

        declaration_link = self.request.app.org.meta.get('declaration_link')
        if declaration_link:
            self.declaration_of_authorization.description = declaration_link

        self.hide(self.drive_distance)

        # populate custom texts
        locale = self.request.locale.split('_')[0] if (
            self.request.locale) else None
        locale = 'de' if locale == 'de' else 'en'

        self.admission_course_agreement.label.text = get_custom_text(
            self.request,
            f'({locale}) Custom admission course agreement'
        )
        self.confirm_name_reveal.label.text = get_custom_text(
            self.request,
            f'({locale}) Custom confirm name reveal'
        )
        self.admission_hint.text = get_custom_text(
            self.request,
            f'({locale}) Custom documents hint'
        )
        self.documents_hint.text = get_custom_text(
            self.request,
            f'({locale}) Custom documents hint'
        )

    def get_translator_data(self) -> dict[str, Any]:
        data = self.get_useful_data()
        result = {
            key: data.get(key) for key in (
                'last_name',
                'first_name',
                'gender',
                'date_of_birth',
                'nationalities',
                'coordinates',
                'address',
                'zip_code',
                'city',
                'hometown',
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
                'profession',
                'occupation',
                'expertise_professional_guilds',
                'expertise_professional_guilds_other',
                'expertise_interpreting_types',
                'agency_references',
            )
        }
        result['state'] = 'proposed'
        result['mother_tongues'] = self.mother_tongues
        result['spoken_languages'] = self.spoken_languages
        result['written_languages'] = self.written_languages
        result['monitoring_languages'] = self.monitoring_languages
        result['date_of_application'] = date.today()
        result['admission'] = 'uncertified'

        return result

    def get_files(self) -> list[File]:

        def as_file(field: UploadField, category: str) -> File | None:
            name = self.request.translate(field.label.text)
            name = name.replace(' (PDF)', '')
            if field.data:
                return File(  # type:ignore[misc]
                    id=random_token(),
                    name=f'{name}.pdf',
                    note=category,
                    reference=FileIntent(
                        BytesIO(dictionary_to_binary(
                            field.data  # type:ignore[arg-type]
                        )),
                        field.data['filename'],
                        field.data['mimetype']
                    )
                )
            return None

        result = [
            as_file(self.declaration_of_authorization, 'Antrag'),
            as_file(self.letter_of_motivation, 'Antrag'),
            as_file(self.resume, 'Antrag'),
            as_file(self.certificates, 'Diplome und Zertifikate'),
            as_file(self.social_security_card, 'Antrag'),
            as_file(self.passport, 'Antrag'),
            as_file(self.passport_photo, 'Antrag'),
            as_file(self.debt_collection_register_extract, 'Abklärungen'),
            as_file(self.criminal_register_extract, 'Abklärungen'),
            as_file(self.certificate_of_capability, 'Abklärungen'),
            as_file(self.confirmation_compensation_office, 'Abklärungen'),
        ]
        return [r for r in result if r is not None]

    def get_ticket_data(self) -> dict[str, Any]:
        data = self.get_useful_data()
        return {
            key: data.get(key) for key in (
                'marital_status',
                'admission_course_completed',
                'admission_course_agreement',
                'remarks',
            )
        }


class GrantAccreditationForm(Form):

    callout = _('Create a user account and publish the translator.')


class RefuseAccreditationForm(Form):

    callout = _('Delete all related data.')
