from onegov.directory import DirectoryConfiguration
from onegov.form import Form
from onegov.form.validators import ValidFormDefinition
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from wtforms import StringField, TextAreaField, validators


class DirectoryForm(Form):
    """ Form for directories. """

    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this form is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))

    structure = TextAreaField(
        label=_("Definition"),
        validators=[
            validators.InputRequired(),
            ValidFormDefinition(require_email_field=False)
        ],
        render_kw={'rows': 32, 'data-editor': 'form'})

    configuration = TextAreaField(
        label=_("Configuration"),
        validators=[validators.InputRequired()],
        render_kw={'rows': 32, 'data-editor': 'yaml'})

    def populate_obj(self, obj):
        super().populate_obj(obj, exclude={'configuration'})
        obj.configuration = DirectoryConfiguration.from_yaml(
            self.configuration.data
        )

    def process_obj(self, obj):
        self.configuration.data = obj.configuration.to_yaml()
