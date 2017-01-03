from onegov.form import Form
from onegov.org import _
from onegov.org.forms.fields import HtmlField
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


class PageForm(PageBaseForm):
    """ Defines the form for pages with the 'page' trait. """

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))
