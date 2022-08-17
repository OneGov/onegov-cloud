from onegov.form import Form
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import ChangeAdjacencyListUrlForm
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(
        label=_("Title"),
        validators=[InputRequired()],
        render_kw={'autofocus': ''}
    )


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(
        label=_("URL"),
        validators=[InputRequired()],
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

    lead_when_child = BooleanField(
        label=_('Show the lead if accessing the parent page'),
        description=_("(Redesign only)")
    )


class PageUrlForm(ChangeAdjacencyListUrlForm):

    def get_model(self):
        return self.model.page
