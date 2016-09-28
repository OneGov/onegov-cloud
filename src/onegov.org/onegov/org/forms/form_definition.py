from onegov.core.html import sanitize_html
from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.utils import annotate_html
from wtforms import StringField, TextAreaField, validators


class FormDefinitionBaseForm(Form):
    """ Form to edit defined forms. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        render_kw={'rows': 4})

    text = TextAreaField(
        label=_("Text"),
        render_kw={'class_': 'editor'},
        filters=[sanitize_html, annotate_html])


class CustomDefinitionForm(FormDefinitionBaseForm):
    """ Same as the default form definition form, but with the definition
    made read-only.

    """

    definition = TextAreaField(
        label=_("Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'}
    )
