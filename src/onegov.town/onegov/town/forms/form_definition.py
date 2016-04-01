from onegov.core.utils import sanitize_html
from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.town import _
from onegov.town.utils import annotate_html
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


class BuiltinDefinitionForm(FormDefinitionBaseForm):
    """ Form to edit builtin forms. """

    definition = TextAreaField(
        label=_("Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        render_kw={
            'rows': 24,
            'readonly': 'readonly',
            'data-editor': 'form'
        }
    )


class CustomDefinitionForm(FormDefinitionBaseForm):
    """ Same as the default form definition form, but with the definition
    made read-only.

    """

    definition = TextAreaField(
        label=_("Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        render_kw={'rows': 32, 'data-editor': 'form'}
    )
