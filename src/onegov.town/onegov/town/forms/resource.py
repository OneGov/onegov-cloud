from onegov.core.utils import sanitize_html
from onegov.form import Form, with_options
from onegov.form.validators import ValidFormDefinition
from onegov.town import _
from onegov.town.utils import mark_images
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import DateField
from wtforms.widgets import TextArea


class ResourceForm(Form):
    """ Defines the form for all resources. """
    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this reservation resource is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_("Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html, mark_images])

    definition = TextAreaField(
        label=_("Extra Fields Definition"),
        validators=[
            validators.Optional(),
            ValidFormDefinition(require_email_field=False)
        ],
        widget=with_options(TextArea, rows=32, **{'data-editor': 'form'}),
    )

    def update_model(self, model):
        """ Stores the form values on the page. """
        model.title = self.title.data
        model.meta = {
            'lead': self.lead.data
        }
        model.content = {
            'text': self.text.data
        }
        model.definition = self.definition.data

    def apply_model(self, model):
        """ Stores the page values on the form. """
        self.title.data = model.title
        self.lead.data = model.meta.get('lead', '')
        self.text.data = model.content.get('text', '')
        self.definition.data = model.definition or ""


class ResourceCleanupForm(Form):
    """ Defines the form to remove multiple allocations. """

    start = DateField(
        label=_("Start"),
        validators=[validators.InputRequired()]
    )

    end = DateField(
        label=_("End"),
        validators=[validators.InputRequired()]
    )

    def validate(self):
        result = super(ResourceCleanupForm, self).validate()

        if self.start.data > self.end.data:
            message = _("The end date must be later than the start date")
            self.end.errors.append(message)
            result = False

        return result
