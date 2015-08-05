from onegov.core.utils import sanitize_html
from onegov.form import Form, with_options
from onegov.town import _
from onegov.town.utils import mark_images
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired, NumberRange
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

    first_hour = IntegerField(
        label=_("First hour shown in calendar"),
        validators=[InputRequired(), NumberRange(0, 24)],
        default=7
    )

    last_hour = IntegerField(
        label=_("First hour shown in calendar"),
        validators=[InputRequired(), NumberRange(0, 24)],
        default=18
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
        model.first_hour = self.first_hour.data
        model.last_hour = self.last_hour.data

    def apply_model(self, model):
        """ Stores the page values on the form. """
        self.title.data = model.title
        self.lead.data = model.meta.get('lead', '')
        self.text.data = model.content.get('text', '')
        self.first_hour.data = model.first_hour
        self.last_hour.data = model.last_hour
