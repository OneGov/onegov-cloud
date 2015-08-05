from onegov.core.utils import sanitize_html
from onegov.form import Form, with_options
from onegov.town import _
from onegov.town.utils import mark_images
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(_("Title"), [validators.InputRequired()])


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(_("URL"), [validators.InputRequired()])

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
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
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
