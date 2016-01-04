from onegov.core.utils import sanitize_html
from onegov.form import Form
from onegov.town import _
from onegov.town.utils import mark_images
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(
        label=_("Title"),
        validators=[validators.InputRequired()],
        render_kw={'autofocus': ''}
    )


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(
        label=_("URL"),
        validators=[validators.InputRequired()],
        render_kw={'class_': 'image-url file-url internal-url'}
    )

    def update_model(self, model):
        """ Stores the form values on the page. """
        model.title = self.title.data
        model.content = {'url': self.url.data}

    def apply_model(self, model):
        """ Stores the page values on the form. """
        self.title.data = model.title
        self.url.data = model.content.get('url')


class PageForm(PageBaseForm):
    """ Defines the form for pages with the 'page' trait. """
    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        render_kw={'rows': 4})

    text = TextAreaField(
        label=_("Text"),
        render_kw={'class_': 'editor'},
        filters=[sanitize_html, mark_images])

    def update_model(self, model):
        """ Stores the form values on the page. """
        model.title = self.title.data
        model.content = {
            'lead': self.lead.data,
            'text': self.text.data
        }

    def apply_model(self, model):
        """ Stores the page values on the form. """
        self.title.data = model.title
        self.lead.data = model.content.get('lead', '')
        self.text.data = model.content.get('text', '')
