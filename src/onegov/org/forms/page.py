from sqlalchemy.orm import object_session

from onegov.core.utils import normalize_for_url
from onegov.form import Form
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from wtforms import StringField, TextAreaField, validators, BooleanField
from wtforms.fields.html5 import URLField

from onegov.page import Page


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

    lead_when_child = BooleanField(
        label=_('Show the lead if accessing the parent page'),
        description=_("(Redesign only)")
    )


class PageUrlForm(Form):

    name = StringField(
        label=_('Url path'),
        validators=[validators.InputRequired()]
    )

    test = BooleanField(
        label=_('Test'),
        default=True
    )

    def ensure_correct_name(self):
        if not self.name.data:
            return

        normalized_name = normalize_for_url(self.name.data)
        if not self.name.data == normalized_name:
            self.name.errors.append(
                _('Invalid name. A valid suggestion is: ${name}',
                  mapping={'name': normalized_name})
            )
            return False

        page = self.model.page
        duplicate_text = _("An entry with the same name exists")
        if not page.parent_id:
            query = object_session(page).query(Page)
            duplicate = query.filter(
                Page.parent_id == None,
                Page.name == normalized_name
            ).first()

            if duplicate:
                self.name.errors.append(duplicate_text)
                return False
            return

        for child in page.parent.children:
            if child == self.model:
                continue
            if child.name == self.name.data:
                self.name.errors.append(duplicate_text)
                return False
