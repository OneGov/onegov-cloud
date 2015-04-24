""" Implements the adding/editing/removing of pages. """

import morepath

from onegov.core.security import Private
from onegov.form import Form, with_options
from onegov.page import PageCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import EditorLayout
from onegov.town.model import LinkEditor, PageEditor
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


class BaseForm(Form):
    title = StringField(_(u"Title"), [validators.InputRequired()])


class LinkForm(BaseForm):
    url = URLField(_(u"URL"), [validators.InputRequired()])


class PageForm(BaseForm):
    lead = TextAreaField(
        _(u"Lead"), widget=with_options(TextArea, rows=4))
    text = TextAreaField(
        _(u"Text"), widget=with_options(TextArea, class_='markdown'))


@TownApp.form(
    model=PageEditor, form=PageForm, template='form.pt', permission=Private
)
def handle_page_form(self, request, form):

    request.include('markdown-editor')
    request.include('markdown-editor-theme')

    if self.action == 'new':
        return handle_new_page(self, request, form, page_type='page')
    elif self.action == 'edit':
        return handle_edit_page(self, request, form, page_type='page')
    else:
        raise NotImplementedError


@TownApp.form(
    model=LinkEditor, form=LinkForm, template='form.pt', permission=Private
)
def handle_link_form(self, request, form):

    if self.action == 'new':
        return handle_new_page(self, request, form, page_type='link')
    elif self.action == 'edit':
        return handle_edit_page(self, request, form, page_type='link')
    else:
        raise NotImplementedError


def handle_new_page(self, request, form, page_type):
    assert page_type in {'page', 'link'}

    if page_type == 'page':
        site_title = _(u"New Page")
    else:
        site_title = _(u"New Link")

    if form.submitted(request):
        pages = PageCollection(request.app.session())

        if page_type == 'page':
            meta = {'type': 'page'}
            content = {
                'lead': form.lead.data,
                'text': form.text.data
            }
            message = _(u"Added a new page.")
        else:
            meta = {'type': 'link'}
            content = {'url': form.url.data}
            message = _(u"Added a new link.")

        page = pages.add(
            parent=self.page,
            title=form.title.data,
            meta=meta,
            content=content
        )

        request.success(message)

        return morepath.redirect(request.link(page))

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form
    }


def handle_edit_page(self, request, form, page_type):
    assert page_type in {'page', 'link'}

    if form.submitted(request):
        self.page.title = form.title.data

        if page_type in {'page', 'town-root'}:
            self.page.content['lead'] = form.lead.data
            self.page.content['text'] = form.text.data
        else:
            self.page.content['url'] = form.url.data

        request.success(_(u"Your changes were saved."))

        return morepath.redirect(request.link(self.page))
    else:
        form.title.data = self.page.title

        if page_type == 'page':
            site_title = _(u"Edit Page")
            form.lead.data = self.page.content.get('lead', '')
            form.text.data = self.page.content.get('text', '')
        else:
            site_title = _(u"Edit Link")
            form.url.data = self.page.content.get('url', '')

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form
    }
