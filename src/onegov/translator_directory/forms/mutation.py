from cached_property import cached_property
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.validators import Stdnum
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.translator_directory import _
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.layout import DefaultLayout
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField
# from wtforms.fields.html5 import EmailField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import Optional


BOOLS = [('True', _('Yes')), ('False', _('No'))]


class TranslatorMutationForm(Form):

    callout = _(
        "This form can be used to report mutations to the data. "
        "You can either leave us a message or directly suggest changes to "
        "the corresponding fields."
    )

    @cached_property
    def language_choices(self):
        languages = LanguageCollection(self.request.session)
        return [
            (str(language.id), language.name)
            for language in languages.query()
        ]

    @cached_property
    def certificate_choices(self):
        certificates = LanguageCertificateCollection(self.request.session)
        return [
            (str(certificate.id), certificate.name)
            for certificate in certificates.query()
        ]

    def on_request(self):
        self.mother_tongues.choices = self.language_choices
        self.spoken_languages.choices = self.language_choices
        self.written_languages.choices = self.language_choices
        self.certificates.choices = self.certificate_choices

        layout = DefaultLayout(self.model, self.request)
        for name, field in self.proposal_fields.items():
            if not layout.show(name):
                self.delete_field(name)
                continue

            value = getattr(self.model, name)
            if isinstance(field, ChosenSelectField):
                field.choices.insert(0, ('', ''))
                field.choices = [
                    (choice[0], self.request.translate(choice[1]))
                    for choice in field.choices
                ]
                field.description = dict(field.choices).get(str(value), '')
            elif isinstance(field, ChosenSelectMultipleField):
                field.choices.insert(0, ('', ''))
                field.choices = [
                    (choice[0], self.request.translate(choice[1]))
                    for choice in field.choices
                ]
                field.description = ', '.join([
                    dict(field.choices).get(str(getattr(v, 'id', v)), '')
                    for v in value
                ])
            else:
                field.description = str(value)

    @property
    def proposal_fields(self):
        for fieldset in self.fieldsets:
            if fieldset.label == 'Proposed changes':
                return fieldset.fields.copy()
        return {}

    @property
    def proposed_changes(self):
        def convert(data):
            if isinstance(data, list):
                return data
            return {'None': None, 'True': True, 'False': False}.get(data, data)

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
                and value != getattr(self.model, name)
            )
        }
        return data

    def ensure_has_content(self):
        if not self.submitter_message.data and not self.proposed_changes:
            self.submitter_message.errors.append(
                _(
                    "Please enter a message or suggest some changes "
                    "using the fields below."
                )
            )
            return False

    submitter_message = TextAreaField(
        fieldset=_("Your message"),
        label=_("Message"),
        render_kw={'rows': 8}
    )

    first_name = StringField(
        label=_('First name'),
        fieldset=_("Proposed changes"),
    )

    last_name = StringField(
        label=_('Last name'),
        fieldset=_("Proposed changes"),
    )

    pers_id = IntegerField(
        label=_('Personal ID'),
        fieldset=_("Proposed changes"),
        validators=[Optional()]
    )

    admission = ChosenSelectField(
        label=_('Admission'),
        choices=list(ADMISSIONS.items()),
        fieldset=_("Proposed changes"),
    )

    withholding_tax = ChosenSelectField(
        label=_('Withholding tax'),
        fieldset=_("Proposed changes"),
        choices=BOOLS,
        validators=[Optional()]
    )

    self_employed = ChosenSelectField(
        label=_('Self-employed'),
        fieldset=_("Proposed changes"),
        choices=BOOLS,
        validators=[Optional()]
    )

    gender = ChosenSelectField(
        label=_('Gender'),
        fieldset=_("Proposed changes"),
        choices=list(GENDERS.items()),
        validators=[Optional()]
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_("Proposed changes"),
        validators=[Optional()]
    )

    nationality = StringField(
        label=_('Nationality'),
        fieldset=_("Proposed changes"),
    )

    # todo????
    # coordinates = CoordinatesField(
    #     label=_("Location"),
    #     description=_(
    #         "Search for the exact address to set a marker.
    # The address fields "
    #         "beneath are filled out automatically."
    #     ),
    #     fieldset=_("Address"),
    #     render_kw={'data-map-type': 'marker'}
    # )

    address = StringField(
        label=_('Street and house number'),
        fieldset=_("Proposed changes"),
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_("Proposed changes"),
    )

    city = StringField(
        label=_('City'),
        fieldset=_("Proposed changes"),
    )

    # drive_distance = FloatField(
    #     label=_('Drive distance (km)'),
    #     validators=[Optional()],
    #     fieldset=_('Address'),
    # )

    social_sec_number = StringField(
        label=_('Swiss social security number'),
        validators=[ValidSwissSocialSecurityNumber()],
        fieldset=_("Proposed changes"),
    )

    bank_name = StringField(
        label=_('Bank name'),
        fieldset=_("Proposed changes"),
    )

    bank_address = StringField(
        label=_('Bank address'),
        fieldset=_("Proposed changes"),
    )

    account_owner = StringField(
        label=_('Account owner'),
        fieldset=_("Proposed changes"),
    )

    iban = StringField(
        label=_('IBAN'),
        validators=[Stdnum(format='iban')],
        fieldset=_("Proposed changes"),
    )
    #
    # email = EmailField(
    #     label=_('Email'),
    #     validators=[Optional(), Email()],
    #     fieldset=_('Contact information')
    # )

    tel_mobile = StringField(
        label=_('Mobile Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_("Proposed changes"),
    )

    tel_private = StringField(
        label=_('Private Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_("Proposed changes"),
    )

    tel_office = StringField(
        label=_('Office Phone Number'),
        validators=[ValidPhoneNumber()],
        fieldset=_("Proposed changes"),
    )

    availability = StringField(
        label=_('Availability'),
        fieldset=_("Proposed changes"),
    )

    operation_comments = TextAreaField(
        label=_('Comments on possible field of application'),
        render_kw={'rows': 3},
        fieldset=_("Proposed changes"),
    )

    confirm_name_reveal = ChosenSelectField(
        label=_('Name revealing confirmation'),
        fieldset=_("Proposed changes"),
        choices=BOOLS,
        validators=[Optional()]
    )

    mother_tongues = ChosenSelectMultipleField(
        label=_('Mother tongues'),
        fieldset=_("Proposed changes"),
        choices=[],
        validators=[Optional()]
    )

    spoken_languages = ChosenSelectMultipleField(
        label=_('Spoken languages'),
        fieldset=_("Proposed changes"),
        choices=[],
        validators=[Optional()],
    )

    written_languages = ChosenSelectMultipleField(
        label=_('Written languages'),
        fieldset=_("Proposed changes"),
        choices=[],
        validators=[Optional()],
    )

    expertise_professional_guilds = ChosenSelectMultipleField(
        label=_('Expertise by professional guild'),
        fieldset=_("Proposed changes"),
        choices=list(PROFESSIONAL_GUILDS.items()),
        validators=[Optional()]
    )

    # expertise_professional_guilds_other = TagsField(
    #     label=_('Expertise by professional guild: other')
    # )

    expertise_interpreting_types = ChosenSelectMultipleField(
        label=_('Expertise by interpreting type'),
        fieldset=_("Proposed changes"),
        choices=list(INTERPRETING_TYPES.items()),
        validators=[Optional()]
    )

    agency_references = TextAreaField(
        label=_('Agency references'),
        render_kw={'rows': 3},
        fieldset=_("Proposed changes")
    )

    education_as_interpreter = ChosenSelectField(
        label=_('Education as interpreter'),
        fieldset=_("Proposed changes"),
        choices=BOOLS,
        validators=[Optional()]
    )

    certificates = ChosenSelectMultipleField(
        label=_('Language Certificates'),
        fieldset=_("Proposed changes"),
        choices=[],
        validators=[Optional()],
    )


class ApplyMutationForm(Form):

    changes = MultiCheckboxField(
        label=_("Proposed changes"),
        choices=[]
    )

    def on_request(self):
        choices = self.model.translated(self.request)
        self.changes.choices = tuple(
            (name, f'{label}: {choice}')
            for name, (label, choice) in choices.items()
        )

    def apply_model(self):
        self.changes.data = list(self.model.changes.keys())

    def update_model(self):
        self.model.apply(self.changes.data)
