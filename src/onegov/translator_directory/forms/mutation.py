from functools import cached_property

from wtforms.fields.simple import EmailField

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import TagsField
from onegov.form.validators import Stdnum
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
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
from wtforms.validators import Optional, Email

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.models.mutation import TranslatorMutation
    from onegov.translator_directory.request import TranslatorAppRequest
    from wtforms import Field
    from wtforms.fields.choices import _Choice


BOOLS = [('True', _('Yes')), ('False', _('No'))]


class TranslatorMutationForm(Form, DrivingDistanceMixin):

    request: 'TranslatorAppRequest'

    hints = [
        ('text', _('You can use this form to report mutations.')),
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

    @cached_property
    def language_choices(self) -> list['_Choice']:
        languages = LanguageCollection(self.request.session)
        return [
            (str(language.id), language.name)
            for language in languages.query()
        ]

    @cached_property
    def certificate_choices(self) -> list['_Choice']:
        certificates = LanguageCertificateCollection(self.request.session)
        return [
            (str(certificate.id), certificate.name)
            for certificate in certificates.query()
        ]

    def on_request(self) -> None:
        self.request.include('tags-input')

        self.mother_tongues.choices = self.language_choices.copy()
        self.spoken_languages.choices = self.language_choices.copy()
        self.written_languages.choices = self.language_choices.copy()
        self.monitoring_languages.choices = self.language_choices.copy()
        self.certificates.choices = self.certificate_choices.copy()

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
    def proposal_fields(self) -> dict[str, 'Field']:
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
        if not self.submitter_message.data and not self.proposed_changes:
            assert isinstance(self.submitter_message.errors, list)
            self.submitter_message.errors.append(
                _(
                    'Please enter a message or suggest some changes '
                    'using the fields below.'
                )
            )
            return False
        return True

    submitter_message = TextAreaField(
        fieldset=_('Your message'),
        label=_('Message'),
        render_kw={'rows': 8}
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

    nationality = StringField(
        label=_('Nationality'),
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
        validators=[ValidSwissSocialSecurityNumber(), Optional()],
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

    model: 'TranslatorMutation'
    request: 'TranslatorAppRequest'

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
