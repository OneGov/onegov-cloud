from onegov.agency import _
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField


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
                return fieldset.fields
        return {}

    @property
    def proposed_changes(self):
        return {
            name: field.data
            for name, field in self.proposal_fields.items()
            if field.data
        }

    def ensure_has_content(self):
        if not self.submitter_message.data:
            if not any((f.data for f in self.proposal_fields.values())):
                self.submitter_message.errors.append(
                    _(
                        "Please enter a message or suggest some changes "
                        "using the fields below."
                    )
                )
                return False

    def on_request(self):
        for name, field in self.proposal_fields.items():
            field.description = getattr(self.model, name)

    # pers_id = IntegerField(
    #     label=_('Personal ID'),
    #     validators=[Optional()]
    # )
    #
    # admission = RadioField(
    #     label=_('Admission'),
    #     choices=tuple(
    #         (id_, label) for id_, label in ADMISSIONS.items()
    #     ),
    #     default=list(ADMISSIONS)[0]
    # )
    #
    # withholding_tax = BooleanField(
    #     label=_('Withholding tax'),
    #     default=False
    # )
    #
    # self_employed = BooleanField(
    #     label=_('Self-employed'),
    #     default=False
    # )

    last_name = StringField(
        label=_('Last name'),
        # validators=[InputRequired()],
        fieldset=_("Proposed changes"),
    )

    first_name = StringField(
        label=_('First name'),
        # validators=[InputRequired()],
        fieldset=_("Proposed changes"),
    )

    # gender = SelectField(
    #     label=_('Gender'),
    #     validators=[StrictOptional()],
    #     choices=[],
    #     fieldset=_('Personal Information')
    # )
    #
    # date_of_birth = DateField(
    #     label=_('Date of birth'),
    #     validators=[Optional()],
    #     fieldset=_('Personal Information')
    # )
    #
    # nationality = StringField(
    #     label=_('Nationality'),
    #     validators=[Optional()],
    #     fieldset=_('Personal Information')
    # )
    #
    # coordinates = CoordinatesField(
    #     label=_("Location"),
    #     description=_(
    #         "Search for the exact address to set a marker. The address fields "
    #         "beneath are filled out automatically."
    #     ),
    #     fieldset=_("Address"),
    #     render_kw={'data-map-type': 'marker'}
    # )
    #
    # address = StringField(
    #     label=_('Street and house number'),
    #     fieldset=_('Address')
    # )
    #
    # zip_code = StringField(
    #     label=_('Zip Code'),
    #     fieldset=_('Address')
    # )
    #
    # city = StringField(
    #     label=_('City'),
    #     fieldset=_('Address')
    # )
    #
    # drive_distance = FloatField(
    #     label=_('Drive distance (km)'),
    #     validators=[Optional()],
    #     fieldset=_('Address'),
    # )
    #
    # social_sec_number = StringField(
    #     label=_('Swiss social security number'),
    #     validators=[Optional(), ValidSwissSocialSecurityNumber()],
    #     fieldset=_('Identification / bank account')
    # )
    #
    # bank_name = StringField(
    #     label=_('Bank name')
    # )
    #
    # bank_address = StringField(
    #     label=_('Bank address')
    # )
    #
    # account_owner = StringField(
    #     label=_('Account owner')
    # )
    #
    # iban = StringField(
    #     label=_('IBAN'),
    #     validators=[Optional(), Stdnum(format='iban')]
    # )
    #
    # email = EmailField(
    #     label=_('Email'),
    #     validators=[Optional(), Email()],
    #     fieldset=_('Contact information')
    # )
    #
    # tel_mobile = StringField(
    #     label=_('Mobile Number'),
    #     validators=[Optional(), ValidPhoneNumber()],
    # )
    #
    # tel_private = StringField(
    #     label=_('Private Phone Number'),
    #     validators=[Optional(), ValidPhoneNumber()],
    # )
    #
    # tel_office = StringField(
    #     label=_('Office Phone Number'),
    #     validators=[Optional(), ValidPhoneNumber()],
    # )
    #
    # availability = StringField(
    #     label=_('Availability'),
    # )
    #
    # operation_comments = TextAreaField(
    #     label=_('Comments on possible field of application'),
    #     render_kw={'rows': 3}
    # )
    #
    # confirm_name_reveal = BooleanField(
    #     label=_('Name revealing confirmation'),
    #     fieldset=_('Legal information'),
    #     description=_('Consent to the disclosure of the name '
    #                   'to other persons and authorities')
    # )
    #
    # date_of_application = DateField(
    #     label=_('Date of application'),
    #     validators=[Optional()],
    #     fieldset=_('Admission to the directory')
    # )
    #
    # date_of_decision = DateField(
    #     label=_('Date of decision'),
    #     validators=[Optional()],
    # )
    #
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
    #
    # proof_of_preconditions = StringField(
    #     label=_('Proof of preconditions')
    # )
    #
    # agency_references = TextAreaField(
    #     label=_('Agency references'),
    #     validators=[InputRequired()],
    #     render_kw={'rows': 3}
    # )
    #
    # education_as_interpreter = BooleanField(
    #     label=_('Education as interpreter'),
    #     default=False
    # )
    #
    # certificates_ids = ChosenSelectMultipleField(
    #     label=_('Language Certificates'),
    #     validators=[Optional()],
    #     choices=[]
    # )
    #
    # comments = TextAreaField(
    #     label=_('Comments')
    # )
    #
    # for_admins_only = BooleanField(
    #     label=_('Hidden'),
    #     default=False
    # )


class ApplyMutationForm(Form):

    changes = MultiCheckboxField(
        label=_("Proposed changes"),
        choices=[]
    )

    def on_request(self):
        def translate(name):
            return self.request.translate(self.model.labels.get(name, name))

        self.changes.choices = tuple(
            (name, f'{translate(name)}: {value}')
            for name, value in self.model.changes.items()
        )

    def apply_model(self):
        self.changes.data = list(self.model.changes.keys())

    def update_model(self):
        self.model.apply(self.changes.data)
