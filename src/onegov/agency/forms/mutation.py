from __future__ import annotations

from onegov.agency import _
from onegov.core.utils import ensure_scheme
from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import MultiCheckboxField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import Email
from wtforms.validators import InputRequired


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from weakref import CallableProxyType
    from wtforms import Field


class MutationForm(Form):

    callout = _(
        'This form can be used to report mutations to the data. '
        'You can either leave us a message or directly suggest changes to '
        'the corresponding fields.'
    )

    delay = HoneyPotField()

    submitter_email = EmailField(
        fieldset=_('Your contact details'),
        label=_('E-Mail'),
        description='max.muster@example.org',
        validators=[InputRequired(), Email()],
    )

    submitter_message = TextAreaField(
        fieldset=_('Your message'),
        label=_('Message'),
        render_kw={'rows': 8}
    )

    @property
    def proposal_fields(self) -> dict[str, CallableProxyType[Field]]:
        for fieldset in self.fieldsets:
            if fieldset.label == 'Proposed changes':
                return fieldset.fields
        return {}

    @property
    def proposed_changes(self) -> dict[str, Any]:
        return {
            name: field.data
            for name, field in self.proposal_fields.items()
            if field.data
        }

    def ensure_has_content(self) -> bool | None:
        if (
            not self.submitter_message.data
            and not any(f.data for f in self.proposal_fields.values())
        ):
            assert isinstance(self.submitter_message.errors, list)
            self.submitter_message.errors.append(
                _(
                    'Please enter a message or suggest some changes '
                    'using the fields below.'
                )
            )
            return False
        return None

    def on_request(self) -> None:
        if self.model is None:
            return

        for name, field in self.proposal_fields.items():
            field.description = getattr(self.model, name)  # type:ignore


class AgencyMutationForm(MutationForm):
    """ Form to report a mutation of an organization. """

    title = StringField(
        fieldset=_('Proposed changes'),
        label=_('Title'),
    )

    location_address = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Location address'),
        render_kw={'rows': 2}
    )

    location_code_city = StringField(
        fieldset=_('Proposed changes'),
        label=_('Location Code and City'),
    )

    postal_address = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Postal address'),
        render_kw={'rows': 2}
    )

    postal_code_city = StringField(
        fieldset=_('Proposed changes'),
        label=_('Postal Code and City'),
    )

    phone = StringField(
        fieldset=_('Proposed changes'),
        label=_('Phone')
    )

    phone_direct = StringField(
        fieldset=_('Proposed changes'),
        label=_('Direct Phone Number or Mobile')
    )

    email = EmailField(
        fieldset=_('Proposed changes'),
        label=_('E-Mail')
    )

    website = StringField(
        fieldset=_('Proposed changes'),
        label=_('Website'),
        filters=(ensure_scheme, )
    )

    opening_hours = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Opening hours'),
        render_kw={'rows': 3}
    )


class PersonMutationForm(MutationForm):
    """ Form to report a mutation of a person. """

    salutation = StringField(
        fieldset=_('Proposed changes'),
        label=_('Salutation')
    )

    academic_title = StringField(
        fieldset=_('Proposed changes'),
        label=_('Academic Title')
    )

    first_name = StringField(
        fieldset=_('Proposed changes'),
        label=_('First name')
    )

    last_name = StringField(
        fieldset=_('Proposed changes'),
        label=_('Last name')
    )

    function = StringField(
        fieldset=_('Proposed changes'),
        label=_('Function')
    )

    email = EmailField(
        fieldset=_('Proposed changes'),
        label=_('E-Mail')
    )

    phone = StringField(
        fieldset=_('Proposed changes'),
        label=_('Phone')
    )

    phone_direct = StringField(
        fieldset=_('Proposed changes'),
        label=_('Direct Phone Number or Mobile')
    )

    born = StringField(
        fieldset=_('Proposed changes'),
        label=_('Born')
    )

    profession = StringField(
        fieldset=_('Proposed changes'),
        label=_('Profession')
    )

    political_party = StringField(
        fieldset=_('Proposed changes'),
        label=_('Political Party')
    )

    parliamentary_group = StringField(
        fieldset=_('Proposed changes'),
        label=_('Parliamentary Group')
    )

    website = StringField(
        fieldset=_('Proposed changes'),
        label=_('Website'),
        filters=(ensure_scheme, )
    )

    website_2 = StringField(
        fieldset=_('Proposed changes'),
        label=_('Website 2'),
        filters=(ensure_scheme, )
    )

    location_address = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Location address'),
        render_kw={'rows': 2}
    )

    location_code_city = StringField(
        fieldset=_('Proposed changes'),
        label=_('Location Code and City'),
    )

    postal_address = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Postal address'),
        render_kw={'rows': 2}
    )

    postal_code_city = StringField(
        fieldset=_('Proposed changes'),
        label=_('Postal Code and City'),
    )

    notes = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Notes'),
        render_kw={'rows': 5}
    )


class ApplyMutationForm(Form):

    changes = MultiCheckboxField(
        label=_('Proposed changes'),
        choices=[]
    )

    def on_request(self) -> None:
        def translate(name: str) -> str:
            return self.request.translate(self.model.labels.get(name, name))

        self.changes.choices = [
            (name, f'{translate(name)}: {value}')
            for name, value in self.model.changes.items()
        ]

    def apply_model(self) -> None:
        self.changes.data = list(self.model.changes.keys())

    def update_model(self) -> None:
        self.model.apply(self.changes.data)
