from onegov.agency import _
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import MultiCheckboxField
from onegov.form.validators import Stdnum
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import ValidSwissSocialSecurityNumber
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import full_text_max_chars
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.layout import DefaultLayout
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import EmailField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import Optional


class TranslatorMutationForm(Form):

    callout = _(
        "This form can be used to report mutations to the data. "
        "You can either leave us a message or directly suggest changes to "
        "the corresponding fields."
    )

    submitter_message = TextAreaField(
        fieldset=_("Your message"),
        label=_("Message"),
        render_kw={'rows': 8}
    )

    @property
    def proposal_fields(self):
        for fieldset in self.fieldsets:
            if fieldset.label == 'Proposed changes':
                return fieldset.fields.copy()
        return {}

    @property
    def proposed_changes(self):
        def convert(data):
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

    def on_request(self):
        layout = DefaultLayout(self.model, self.request)
        for name, field in self.proposal_fields.items():
            if not layout.show(name):
                self.delete_field(name)
                continue

            value = getattr(self.model, name)
            if isinstance(field, ChosenSelectField):
                field.choices = [
                    (choice[0], self.request.translate(choice[1]))
                    for choice in field.choices
                ]
                field.choices.insert(0, ('', ''))
                field.default = ''
                field.description = dict(field.choices).get(str(value), '')
            else:
                field.description = str(value)

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
        choices=tuple(ADMISSIONS.items()),
        fieldset=_("Proposed changes"),
    )

    withholding_tax = ChosenSelectField(
        label=_('Withholding tax'),
        fieldset=_("Proposed changes"),
        choices=(('True', _("Yes")), ('False', _("No"))),
        validators=[Optional()]
    )

    self_employed = ChosenSelectField(
        label=_('Self-employed'),
        fieldset=_("Proposed changes"),
        choices=(('True', _("Yes")), ('False', _("No"))),
        validators=[Optional()]
    )

    gender = ChosenSelectField(
        label=_('Gender'),
        fieldset=_("Proposed changes"),
        choices=tuple(GENDERS.items()),
        validators=[Optional()]
    )

    # date_of_birth = DateField(
    #     label=_('Date of birth'),
    #     fieldset=_("Proposed changes"),
    # )

    nationality = StringField(
        label=_('Nationality'),
        fieldset=_("Proposed changes"),
    )

    # todo????
    # coordinates = CoordinatesField(
    #     label=_("Location"),
    #     description=_(
    #         "Search for the exact address to set a marker. The address fields "
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
        choices=(('True', _("Yes")), ('False', _("No"))),
        validators=[Optional()]
    )

    # mother_tongues_ids = ChosenSelectMultipleField(
    #     label=_('Mother tongues'),
    #     validators=[InputRequired()],
    #     choices=[],
    #     fieldset=_('Language training and expertise')
    # )
    #
    # spoken_languages_ids = ChosenSelectMultipleField(
    #     label=_('Spoken languages'),
    #     validators=[StrictOptional()],
    #     choices=[]
    # )
    #
    # written_languages_ids = ChosenSelectMultipleField(
    #     label=_('Written languages'),
    #     validators=[StrictOptional()],
    #     choices=[]
    # )
    #
    # expertise_professional_guilds = MultiCheckboxField(
    #     label=_('Expertise by professional guild'),
    #     choices=[
    #         (id_, label) for id_, label in PROFESSIONAL_GUILDS.items()
    #     ]
    # )
    #
    # expertise_professional_guilds_other = TagsField(
    #     label=_('Expertise by professional guild: other')
    # )
    #
    # expertise_interpreting_types = MultiCheckboxField(
    #     label=_('Expertise by interpreting type'),
    #     choices=[
    #         (id_, label) for id_, label in INTERPRETING_TYPES.items()
    #     ]
    # )

    agency_references = TextAreaField(
        label=_('Agency references'),
        render_kw={'rows': 3},
        fieldset=_("Proposed changes")
    )

    education_as_interpreter = ChosenSelectField(
        label=_('Education as interpreter'),
        fieldset=_("Proposed changes"),
        choices=(('True', _("Yes")), ('False', _("No"))),
        validators=[Optional()]
    )

    # certificates_ids = ChosenSelectMultipleField(
    #     label=_('Language Certificates'),
    #     validators=[Optional()],
    #     choices=[]
    # )


class ApplyMutationForm(Form):

    changes = MultiCheckboxField(
        label=_("Proposed changes"),
        choices=[]
    )

    def on_request(self):
        def translate(name):
            return self.request.translate(self.model.labels.get(name, name))

        def convert(value):
            if value is True:
                return self.request.translate(_('Yes'))
            if value is False:
                return self.request.translate(_('No'))
            return value

        self.changes.choices = tuple(
            (name, f'{translate(name)}: {convert(value)}')
            for name, value in self.model.changes.items()
        )

    def apply_model(self):
        self.changes.data = list(self.model.changes.keys())

    def update_model(self):
        self.model.apply(self.changes.data)
