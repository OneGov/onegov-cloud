""" Implements the adding/editing/removing of pages. """

import morepath

from onegov.core.security import Private
from onegov.form import Form, with_options
from onegov.page import PageCollection
from onegov.town import _
from onegov.town.utils import sanitize_html
from onegov.town.app import TownApp
from onegov.town.layout import EditorLayout
from onegov.town.models import Editor
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


class BaseForm(Form):
    title = StringField(_("Title"), [validators.InputRequired()])


class LinkForm(BaseForm):
    url = URLField(_("URL"), [validators.InputRequired()])

    def get_content(self):
        return {
            'url': self.url.data
        }

    def set_content(self, page):
        self.url.data = page.content.get('url', '')


class PageForm(BaseForm):
    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html])

    def get_content(self):
        return {
            'lead': self.lead.data,
            'text': self.text.data
        }

    def set_content(self, page):
        self.lead.data = page.content.get('lead', '')
        self.text.data = page.content.get('text', '')


def get_form_class(editor):
    type_info = morepath.settings().pages.type_info
    return type_info[editor.page_type]['form']


@TownApp.form(
    model=Editor, form=get_form_class, template='form.pt', permission=Private)
def handle_page_form(self, request, form):
    if self.action == 'new':
        return handle_new_page(self, request, form, self.page_type)
    elif self.action == 'edit':
        return handle_edit_page(self, request, form, self.page_type)
    else:
        raise NotImplementedError


def handle_new_page(self, request, form, page_type):
    type_info = morepath.settings().pages.type_info

    if form.submitted(request):
        pages = PageCollection(request.app.session())

        page = pages.add(
            parent=self.page,
            title=form.title.data,
            meta={'type': page_type},
            content=form.get_content()
        )

        request.success(type_info[page_type]['new_page_message'])

        return morepath.redirect(request.link(page))

    site_title = type_info[page_type]['new_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form
    }


def handle_edit_page(self, request, form, page_type):
    type_info = morepath.settings().pages.type_info

    if form.submitted(request):
        self.page.title = form.title.data
        self.page.content = form.get_content()

        request.success(_(u"Your changes were saved."))

        return morepath.redirect(request.link(self.page))
    else:
        form.title.data = self.page.title
        form.set_content(self.page)

    site_title = type_info[page_type]['edit_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form
    }
