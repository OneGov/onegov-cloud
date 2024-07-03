from onegov.core.utils import normalize_for_url
from onegov.form import Form, merge_forms, FormDefinitionCollection
from onegov.form.validators import ValidFormDefinition, ValidSurveyDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import PaymentForm
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING


class FormDefinitionBaseForm(Form):
    title = StringField(_("Title"), [InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))

    group = StringField(
        label=_("Group"),
        description=_("Used to group the form in the overview"))

    definition = TextAreaField(
        label=_("Definition"),
        validators=[InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'})

    pick_up = TextAreaField(
        label=_("Pick-Up"),
        description=_("Describes how this resource can be picked up. "
                      "This text is used on the ticket status page to "
                      "inform the user")
    )


if TYPE_CHECKING:
    # we help mypy understand merge_forms this way, eventually we should
    # write a mypy plugin for merge_forms/move_fields, that does the same
    # substitution
    class FormDefinitionForm(FormDefinitionBaseForm, PaymentForm):
        pass
else:
    class FormDefinitionForm(merge_forms(
        FormDefinitionBaseForm,
        PaymentForm
    )):
        pass


class SurveyDefinitionForm(Form):
    """ Form to create surveys. """

    # This class is needed to hide forbidden fields from the form editor
    css_class = 'survey-definition'

    title = StringField(_("Title"), [InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Short description of the survey"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))

    group = StringField(
        label=_("Group"),
        description=_("Used to group the form in the overview"))

    definition = TextAreaField(
        label=_("Definition"),
        validators=[InputRequired(), ValidSurveyDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'})


class FormDefinitionUrlForm(Form):

    name = StringField(
        label=_('URL path'),
        validators=[InputRequired()]
    )

    def ensure_correct_name(self) -> bool | None:
        if not self.name.data:
            return None

        assert isinstance(self.name.errors, list)
        if self.model.name == self.name.data:
            self.name.errors.append(
                _('Please fill out a new name')
            )
            return False

        normalized_name = normalize_for_url(self.name.data)
        if not self.name.data == normalized_name:
            self.name.errors.append(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )
            return False

        other_entry = FormDefinitionCollection(self.request.session).by_name(
            normalized_name)
        if other_entry:
            self.name.errors.append(_("An entry with the same name exists"))
            return False
        return None
