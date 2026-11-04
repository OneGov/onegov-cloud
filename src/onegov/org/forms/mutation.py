from markupsafe import Markup
from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.form.fields import MultiCheckboxField
from wtforms.fields import EmailField
from wtforms.fields import SelectChoice
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import Email
from wtforms.validators import InputRequired


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
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
    def proposal_fields(self) -> Mapping[str, Field]:
        for fieldset in self.fieldsets:
            if fieldset.label == 'Proposed changes':
                return fieldset.fields
        return {}

    @property
    def proposed_changes(self) -> dict[str, Any]:
        return {
            name: field.data
            for name, field in self.proposal_fields.items()
            if field.data != getattr(self.model, name)
        }

    def ensure_has_content(self) -> bool | None:
        if (
            not self.submitter_message.data
            and not any(
                field.data != getattr(self.model, name)
                for name, field in self.proposal_fields.items()
            )
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
        if self.model is None or self.request.POST:
            return

        for name, field in self.proposal_fields.items():
            field.data = getattr(self.model, name)


class TopicMutationForm(MutationForm):
    """ Form to report a mutation of a topic. """

    title = StringField(
        fieldset=_('Proposed changes'),
        label=_('Title'),
    )

    lead = TextAreaField(
        fieldset=_('Proposed changes'),
        label=_('Lead'),
        render_kw={'rows': 4}
    )

    text = HtmlField(
        fieldset=_('Proposed changes'),
        label=_('Text')
    )


class ApplyTopicMutationForm(Form):

    changes = MultiCheckboxField(
        label=_('Proposed changes'),
        choices=lambda form, field: [
            SelectChoice(
                name,
                Markup('{}: {}').format(
                    form.request.translate(form.model.labels.get(name, name)),
                    Markup(value) if isinstance(original, Markup) else value  # nosec: B704
                )
            )
            for name in ('title', 'lead', 'text')
            if name in form.model.changes
            if (
                value := form.model.changes[name]
            ) != (original := getattr(
                form.model.target,
                name
            ))
        ]
    )

    def apply_model(self) -> None:
        self.changes.data = list(self.model.changes.keys())

    def update_model(self) -> None:
        self.model.apply(self.changes.data)
