from onegov.agency import _
from onegov.core.utils import ensure_scheme
from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import MultiCheckboxField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators
from wtforms.fields.html5 import EmailField


class MutationForm(Form):

    callout = _(
        "This form can be used to report mutations to the data. "
        "You can either leave us a message or directly suggest changes to "
        "the corresponding fields."
    )

    delay = HoneyPotField()

    submitter_email = EmailField(
        fieldset=_("Your contact details"),
        label=_("E-Mail"),
        description="max.muster@example.org",
        validators=[validators.InputRequired(), validators.Email()],
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


class AgencyMutationForm(MutationForm):
    """ Form to report a mutation of an organization. """

    title = StringField(
        fieldset=_("Proposed changes"),
        label=_("Title"),
    )


class PersonMutationForm(MutationForm):
    """ Form to report a mutation of a person. """

    salutation = StringField(
        fieldset=_("Proposed changes"),
        label=_("Salutation")
    )

    academic_title = StringField(
        fieldset=_("Proposed changes"),
        label=_("Academic Title")
    )

    first_name = StringField(
        fieldset=_("Proposed changes"),
        label=_("First name")
    )

    last_name = StringField(
        fieldset=_("Proposed changes"),
        label=_("Last name")
    )

    function = StringField(
        fieldset=_("Proposed changes"),
        label=_("Function")
    )

    email = EmailField(
        fieldset=_("Proposed changes"),
        label=_("E-Mail")
    )

    phone = StringField(
        fieldset=_("Proposed changes"),
        label=_("Phone")
    )

    phone_direct = StringField(
        fieldset=_("Proposed changes"),
        label=_("Direct Phone Number")
    )

    born = StringField(
        fieldset=_("Proposed changes"),
        label=_("Born")
    )

    profession = StringField(
        fieldset=_("Proposed changes"),
        label=_("Profession")
    )

    political_party = StringField(
        fieldset=_("Proposed changes"),
        label=_("Political Party")
    )

    parliamentary_group = StringField(
        fieldset=_("Proposed changes"),
        label=_("Parliamentary Group")
    )

    website = StringField(
        fieldset=_("Proposed changes"),
        label=_("Website"),
        filters=(ensure_scheme, )
    )

    address = TextAreaField(
        fieldset=_("Proposed changes"),
        label=_("Address"),
        render_kw={'rows': 5}
    )

    notes = TextAreaField(
        fieldset=_("Proposed changes"),
        label=_("Notes"),
        render_kw={'rows': 5}
    )


class ApplyMutationForm(Form):

    changes = MultiCheckboxField(
        label=_("Proposed changes"),
        choices=[]
    )

    def on_request(self):
        translate = self.request.translate
        labels = self.model.labels
        self.changes.choices = (
            (name, f'{translate(labels[name])}: {value}')
            for name, value in self.model.changes.items()
        )

    def apply_model(self):
        self.changes.data = list(self.model.changes.keys())

    def update_model(self):
        self.model.apply(self.changes.data)
