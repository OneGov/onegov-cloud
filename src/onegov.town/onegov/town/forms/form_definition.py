from onegov.core.utils import sanitize_html
from onegov.form import Form, with_options
from onegov.form.validators import ValidFormDefinition
from onegov.town import _
from onegov.town.utils import mark_images
from wtforms import StringField, TextAreaField, validators
from wtforms.widgets import TextArea


class FormDefinitionBaseForm(Form):
    """ Form to edit defined forms. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html, mark_images])

    def update_model(self, model):
        model.title = self.title.data

        if model.type == 'custom':
            model.definition = self.definition.data

        model.meta['lead'] = self.lead.data
        model.content['text'] = self.text.data

    def apply_model(self, model):
        self.title.data = model.title
        self.definition.data = model.definition
        self.lead.data = model.meta.get('lead', '')
        self.text.data = model.content.get('text', '')


class BuiltinDefinitionForm(FormDefinitionBaseForm):
    """ Form to edit builtin forms. """

    definition = TextAreaField(
        label=_(u"Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        widget=with_options(
            TextArea, rows=24, readonly='readonly',
            **{'data-editor': 'form'}
        ),
    )


class CustomDefinitionForm(FormDefinitionBaseForm):
    """ Same as the default form definition form, but with the definition
    made read-only.

    """

    definition = TextAreaField(
        label=_(u"Definition"),
        validators=[validators.InputRequired(), ValidFormDefinition()],
        widget=with_options(TextArea, rows=32, **{'data-editor': 'form'}),
    )
