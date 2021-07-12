from onegov.core.utils import normalize_for_url
from onegov.form import Form, merge_forms, FormDefinitionCollection
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import PaymentMethodForm
from wtforms import StringField, TextAreaField, validators


class FormDefinitionBaseForm(Form):
    """ Form to edit defined forms. """

    title = StringField(_("Title"), [validators.InputRequired()])

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
        validators=[validators.InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'})


class FormDefinitionForm(merge_forms(
    FormDefinitionBaseForm,
    PaymentMethodForm
)):
    pass


class FormDefinitionUrlForm(Form):

    name = StringField(
        label=_('Url path'),
        validators=[validators.InputRequired()]
    )

    def ensure_correct_name(self):
        if not self.name.data:
            return

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

        duplicate_text = _("An entry with the same name exists")
        other_entry = FormDefinitionCollection(self.request.session).by_name(
            normalized_name)
        if other_entry:
            self.name.errors.append(duplicate_text)
            return False
