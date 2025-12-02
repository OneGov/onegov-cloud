from __future__ import annotations

from depot.io.utils import FileIntent
from functools import cached_property
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.utils import dictionary_to_binary
from onegov.file import File
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import TagsField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit, MIME_TYPES_PDF
from onegov.form.validators import Stdnum
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import Coordinates
from onegov.gis import CoordinatesField
from onegov.translator_directory import _
from onegov.translator_directory.collections.certificate import (
    LanguageCertificateCollection)
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.forms.mixins import DrivingDistanceMixin
from onegov.translator_directory.layout import DefaultLayout
from wtforms.fields import DateField
from wtforms.fields import FloatField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.simple import EmailField
from wtforms.validators import Optional, Email

from typing import Any, TYPE_CHECKING

from onegov.translator_directory.utils import nationality_choices

if TYPE_CHECKING:
    from onegov.translator_directory.models.mutation import TranslatorMutation
    from onegov.translator_directory.request import TranslatorAppRequest
    from wtforms import Field
    from wtforms.fields.choices import _Choice


BOOLS = [('True', _('Yes')), ('False', _('No'))]


class TranslatorMutationForm(Form, DrivingDistanceMixin):

    request: TranslatorAppRequest

    hints = [
        ('bullet', _('You can either leave us a message or directly suggest '
                     'changes in the corresponding fields.')),
        ('bullet', _('You only need to specify the fields that are to be '
                     'changed. The current value is greyed out.')),
        ('bullet', _('Please note that the address must be entered via the '
                     'location.')),
       ('bullet', _('Make sure that if you make multiple selections '
                     '(e.g. languages) you select all options, not just those '
                     'you want changed.')),
        ('bullet', _('Expertise by professional guild (other) can be listed '
                     'comma-separated.')),
        ('bullet', _('If you would like to change the e-mail address, please '
                     'note this in the message.'))
    ]
    locale: str = 'de_CH'

    @cached_property
    def language_choices(self) -> list[_Choice]:
        languages = LanguageCollection(self.request.session)
        return [
            (str(language.id), language.name)
            for language in languages.query()
        ]

    @cached_property
    def certificate_choices(self) -> list[_Choice]:
        certificates = LanguageCertificateCollection(self.request.session)
        return [
            (str(certificate.id), certificate.name)
            for certificate in certificates.query()
        ]

    def on_request(self) -> None:
        self.request.include('tags-input')
        self.locale = self.request.locale if self.request.locale else 'de_CH'

        self.mother_tongues.choices = self.language_choices.copy()
        self.spoken_languages.choices = self.language_choices.copy()
        self.written_languages.choices = self.language_choices.copy()
        self.monitoring_languages.choices = self.language_choices.copy()
        self.certificates.choices = self.certificate_choices.copy()
        self.nationalities.choices = nationality_choices(self.request.locale)

        self.hide(self.drive_distance)

        layout = DefaultLayout(self.model, self.request)
        for name, field in self.proposal_fields.items():
            if not layout.show(name):
                self.delete_field(name)
                continue

            value = getattr(self.model, name)
            if isinstance(field, ChosenSelectField):
                assert isinstance(field.choices, list)
                field.choices.insert(0, ('', ''))
                field.choices = [
                    (choice[0], self.request.translate(choice[1]))
                    for choice in field.choices
                ]
                choice_lookup = dict(field.choices)  # type:ignore
                field.long_description = choice_lookup.get(  # type:ignore
                    str(value), ''
                )
            elif isinstance(field, ChosenSelectMultipleField):
                assert isinstance(field.choices, list)
                field.choices.insert(0, ('', ''))
                field.choices = [
                    (choice[0], self.request.translate(choice[1]))
                    for choice in field.choices
                ]
                choice_lookup = dict(field.choices)  # type:ignore
                field.long_description = ', '.join(  # type:ignore
                    choice_lookup.get(str(getattr(v, 'id', v)), '')
                    for v in value
                )
            elif isinstance(field, CoordinatesField):
                pass
            elif isinstance(field, TagsField):
                field.long_description = ', '.join(value)  # type:ignore
            elif isinstance(field, DateField):
                if value:
                    field.long_description = (  # type:ignore
                        layout.format_date(value, 'date'))
            else:
                field.long_description = str(value or '')  # type:ignore

    @property
    def proposal_fields(self) -> dict[str, Field]:
        for fieldset in self.fieldsets:
            if fieldset.label == 'Proposed changes':
                # NOTE: There's no type checker support for proxy objects
                return fieldset.fields.copy()  # type:ignore
        return {}

    @property
    def proposed_changes(self) -> dict[str, Any]:
        def convert(data: Any) -> Any:
            if isinstance(data, list):
                return data
            if isinstance(data, Coordinates):
                return data if data.lat and data.lon else None
            return {'None': None, 'True': True, 'False': False}.get(data, data)

        def has_changed(name: str, value: Any) -> bool:
            old = getattr(self.model, name)
            if name in ('mother_tongues', 'spoken_languages',
                        'written_languages', 'monitoring_languages',
                        'certificates'):
                old = [str(x.id) for x in getattr(self.model, name, [])]
            return value != old

        data = {
            name: convert(field.data)
            for name, field in self.proposal_fields.items()
        }
        data = {
            name: value for name, value in data.items()
            if (
                value != ''
                and value is not None
                and value != []
                and has_changed(name, value)
            )
        }
        return data

    def ensure_has_content(self) -> bool:
        has_message = bool(self.submitter_message.data)
        has_changes = bool(self.proposed_changes)
        has_docs = any(
            [
                self.declaration_of_authorization.data,
                self.letter_of_motivation.data,
                self.resume.data,
                self.uploaded_certificates.data,
                self.social_security_card.data,
                self.passport.data,
                self.passport_photo.data,
                self.debt_collection_register_extract.data,
                self.criminal_register_extract.data,
                self.certificate_of_capability.data,
                self.confirmation_compensation_office.data,
            ]
        )
        if not has_message and not has_changes and not has_docs:
            assert isinstance(self.submitter_message.errors, list)
            self.submitter_message.errors.append(
                _(
                    'Please enter a message, suggest changes, '
                    'or upload documents.'
                )
            )
            return False
        return True

    def get_files(self) -> list[File]:
        """Convert uploaded files to File objects."""

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
                        field.data['mimetype'],
                    ),
                )
            return None

        result = [
            as_file(self.declaration_of_authorization, 'Mutationsmeldung'),
            as_file(self.letter_of_motivation, 'Mutationsmeldung'),
            as_file(self.resume, 'Mutationsmeldung'),
            as_file(self.uploaded_certificates, 'Mutationsmeldung'),
            as_file(self.social_security_card, 'Mutationsmeldung'),
            as_file(self.passport, 'Mutationsmeldung'),
            as_file(self.passport_photo, 'Mutationsmeldung'),
            as_file(self.debt_collection_register_extract, 'Mutationsmeldung'),
            as_file(self.criminal_register_extract, 'Mutationsmeldung'),
            as_file(self.certificate_of_capability, 'Mutationsmeldung'),
            as_file(self.confirmation_compensation_office, 'Mutationsmeldung'),
        ]
        return [r for r in result if r is not None]

    submitter_message = TextAreaField(
        fieldset=_('Your message'),
        label=_('Message'),
        render_kw={'rows': 8}
    )

    declaration_of_authorization = UploadField(
        label=_('Signed declaration of authorization (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    letter_of_motivation = UploadField(
        label=_('Short letter of motivation (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    resume = UploadField(
        label=_('Resume (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    uploaded_certificates = UploadField(
        label=_('Certificates (PDF)'),
        description=_(
            'For the last five years. Language proficiency certificates '
            'level C2 are mandatory for non-native speakers.'
        ),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    social_security_card = UploadField(
        label=_('Social security card (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    passport = UploadField(
        label=_('Identity card, passport or foreigner identity card (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    passport_photo = UploadField(
        label=_('Current passport photo (PDF)'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    debt_collection_register_extract = UploadField(
        label=_('Current extract from the debt collection register (PDF)'),
        description=_('Maximum 6 months since issue.'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    criminal_register_extract = UploadField(
        label=_('Current extract from the Central Criminal Register (PDF)'),
        description=_(
            'Maximum 6 months since issue. Online order at '
            'www.strafregister.admin.ch'
        ),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    certificate_of_capability = UploadField(
        label=_('Certificate of Capability (PDF)'),
        description=_('Available from the municipal or city administration.'),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    confirmation_compensation_office = UploadField(
        label=_(
            'Confirmation from the compensation office regarding '
            'self-employment'
        ),
        validators=[
            WhitelistedMimeType(MIME_TYPES_PDF),
            FileSizeLimit(100 * 1024 * 1024),
            Optional(),
        ],
        render_kw={'resend_upload': True},
        fieldset=_('Documents'),
    )

    first_name = StringField(
        label=_('First name'),
        fieldset=_('Proposed changes'),
    )

    last_name = StringField(
        label=_('Last name'),
        fieldset=_('Proposed changes'),
    )

    pers_id = IntegerField(
        label=_('Personal ID'),
        fieldset=_('Proposed changes'),
        validators=[Optional()]
    )

    admission = ChosenSelectField(
        label=_('Admission'),
        fieldset=_('Proposed changes'),
        choices=list(ADMISSIONS.items()),
        validators=[Optional()]
    )

    withholding_tax = ChosenSelectField(
        label=_('Withholding tax'),
        fieldset=_('Proposed changes'),
        choices=BOOLS,
        validators=[Optional()]
    )

    self_employed = ChosenSelectField(
        label=_('Self-employed'),
        fieldset=_('Proposed changes'),
        choices=BOOLS,
        validators=[Optional()]
    )

    gender = ChosenSelectField(
        label=_('Gender'),
        fieldset=_('Proposed changes'),
        choices=list(GENDERS.items()),
        validators=[Optional()]
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_('Proposed changes'),
        validators=[Optional()]
    )

    nationalities = ChosenSelectMultipleField(
        label=_('Nationality(ies)'),
        choices=[],  # will be filled in on_request
        fieldset=_('Proposed changes'),
    )

    hometown = StringField(
        label=_('Hometown'),
        fieldset=_('Proposed changes'),
        validators=[Optional()],
    )

    coordinates = CoordinatesField(
        label=_('Location'),
        description=_(
            'Search for the exact address to set a marker. The address fields '
            'beneath are filled out automatically.'
        ),
        fieldset=_('Proposed changes'),
        render_kw={'data-map-type': 'marker'}
    )

    address = StringField(
        label=_('Street and house number'),
        fieldset=_('Proposed changes'),
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_('Proposed changes'),
    )

    city = StringField(
        label=_('City'),
        fieldset=_('Proposed changes'),
    )

    drive_distance = FloatField(
        label=_('Drive distance (km)'),
        fieldset=_('Proposed changes'),
        validators=[Optional()],
    )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[ValidSwissSocialSecurityNumber()],
        fieldset=_('Proposed changes'),
    )

    bank_name = StringField(
        label=_('Bank name'),
        fieldset=_('Proposed changes'),
    )

    bank_address = StringField(
        label=_('Bank address'),
        fieldset=_('Proposed changes'),
    )

    account_owner = StringField(
        label=_('Account owner'),
        fieldset=_('Proposed changes'),
    )

    iban = StringField(
        label=_('IBAN'),
        validators=[Stdnum(format='iban')],
        fieldset=_('Proposed changes'),
    )

    email = EmailField(
        label=_('Email'),
        validators=[Optional(), Email()],
        fieldset=_('Proposed changes'),
    )

    tel_mobile = StringField(
        label=_('Mobile Number'),
        validators=[ValidPhoneNumber(), Optional()],
        fieldset=_('Proposed changes'),
    )

    tel_private = StringField(
        label=_('Private Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_('Proposed changes'),
    )

    tel_office = StringField(
        label=_('Office Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_('Proposed changes'),
    )

    availability = StringField(
        label=_('Availability'),
        fieldset=_('Proposed changes'),
    )

    operation_comments = TextAreaField(
        label=_('Comments on possible field of application'),
        render_kw={'rows': 3},
        fieldset=_('Proposed changes'),
    )

    confirm_name_reveal = ChosenSelectField(
        label=_('Name revealing confirmation'),
        fieldset=_('Proposed changes'),
        choices=BOOLS,
        validators=[Optional()]
    )

    date_of_application = DateField(
        label=_('Date of application'),
        fieldset=_('Proposed changes'),
        validators=[Optional()],
    )

    date_of_decision = DateField(
        label=_('Date of decision'),
        fieldset=_('Proposed changes'),
        validators=[Optional()],
    )

    mother_tongues = ChosenSelectMultipleField(
        label=_('Mother tongues'),
        fieldset=_('Proposed changes'),
        choices=[],
        validators=[Optional()]
    )

    spoken_languages = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        fieldset=_('Proposed changes'),
        choices=[],
        validators=[Optional()],
    )

    written_languages = ChosenSelectMultipleField(
        label=_('Written languages'),
        fieldset=_('Proposed changes'),
        choices=[],
        validators=[Optional()],
    )

    monitoring_languages = ChosenSelectMultipleField(
        label=_('Monitoring languages'),
        fieldset=_('Proposed changes'),
        choices=[],
        validators=[Optional()],
    )

    profession = StringField(
        label=_('Learned profession'),
        fieldset=_('Proposed changes'),
    )

    occupation = StringField(
        label=_('Current professional activity'),
        fieldset=_('Proposed changes'),
    )

    expertise_professional_guilds = ChosenSelectMultipleField(
        label=_('Expertise by professional guild'),
        fieldset=_('Proposed changes'),
        choices=list(PROFESSIONAL_GUILDS.items()),
        validators=[Optional()]
    )

    expertise_professional_guilds_other = TagsField(
        label=_('Expertise by professional guild: other'),
        fieldset=_('Proposed changes'),
    )

    expertise_interpreting_types = ChosenSelectMultipleField(
        label=_('Expertise by interpreting type'),
        fieldset=_('Proposed changes'),
        choices=list(INTERPRETING_TYPES.items()),
        validators=[Optional()]
    )

    proof_of_preconditions = StringField(
        label=_('Proof of preconditions'),
        fieldset=_('Proposed changes'),
    )

    agency_references = TextAreaField(
        label=_('Agency references'),
        render_kw={'rows': 3},
        fieldset=_('Proposed changes')
    )

    education_as_interpreter = ChosenSelectField(
        label=_('Education as interpreter'),
        fieldset=_('Proposed changes'),
        choices=BOOLS,
        validators=[Optional()]
    )

    certificates = ChosenSelectMultipleField(
        label=_('Language Certificates'),
        fieldset=_('Proposed changes'),
        choices=[],
        validators=[Optional()],
    )

    comments = TextAreaField(
        label=_('Comments'),
        fieldset=_('Proposed changes'),
    )


class ApplyMutationForm(Form):

    model: TranslatorMutation
    request: TranslatorAppRequest

    changes = MultiCheckboxField(
        label=_('Proposed changes'),
        choices=[]
    )

    def on_request(self) -> None:
        choices = self.model.translated(self.request)
        self.changes.choices = [
            (name, f'{label}: {choice}')
            for name, (label, choice, original) in choices.items()
        ]

    def apply_model(self) -> None:
        self.changes.data = list(self.model.changes.keys())

    def update_model(self) -> None:
        self.model.apply(self.changes.data or ())
