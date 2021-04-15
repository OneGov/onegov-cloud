""" Implements the adding/editing/removing of pages. """

import morepath
import transaction
from webob.exc import HTTPForbidden

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.forms.page import PageUrlForm
from onegov.org.layout import EditorLayout
from onegov.org.migration import PageNameChange
from onegov.org.models import Clipboard, Editor
from onegov.page import PageCollection


def get_form_class(editor, request):

    src = Clipboard.from_session(request).get_object()

    if src and editor.action == 'paste':
        if src and src.trait in editor.page.allowed_subtraits:
            return editor.page.get_form_class(
                src.trait, editor.action, request)
    if editor.action == 'change-url':
        return PageUrlForm
    return editor.page.get_form_class(editor.trait, editor.action, request)


@OrgApp.form(model=Editor, template='form.pt', permission=Private,
             form=get_form_class)
def handle_page_form(self, request, form, layout=None):
    if self.action == 'new':
        return handle_new_page(self, request, form, layout=layout)
    elif self.action == 'edit':
        return handle_edit_page(self, request, form, layout=layout)
    elif self.action == 'change-url':
        return handle_change_page_url(self, request, form, layout=layout)
    elif self.action == 'paste':
        clipboard = Clipboard.from_session(request)
        src = clipboard.get_object()
        clipboard.clear()

        return handle_new_page(self, request, form, src, layout)
    else:
        raise NotImplementedError


def handle_new_page(self, request, form, src=None, layout=None):
    site_title = self.page.trait_messages[self.trait]['new_page_title']
    if layout:
        layout.site_title = site_title

    if form.submitted(request):
        pages = PageCollection(request.session)
        page = pages.add(
            parent=self.page,
            title=form.title.data,
            type=self.page.type,
            meta={'trait': self.trait}
        )
        form.populate_obj(page)

        request.success(page.trait_messages[page.trait]['new_page_added'])
        return morepath.redirect(request.link(page))

    if src:
        form.process(obj=src)

    return {
        'layout': layout or EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_edit_page(self, request, form, layout=None):
    site_title = self.page.trait_messages[self.trait]['edit_page_title']
    if layout:
        layout.site_title = site_title

    if form.submitted(request):
        form.populate_obj(self.page)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self.page))
    elif not request.POST:
        form.process(obj=self.page)

    return {
        'layout': layout or EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_change_page_url(self, request, form, layout=None):
    if not request.is_admin:
        return HTTPForbidden()

    subpage_count = 0

    def count_page(page):
        nonlocal subpage_count
        subpage_count += 1
        for child in page.children:
            count_page(child)

    for child in self.page.children:
        count_page(child)

    messages = [
        _('Stable urls are important. Here you can change the '
          'path to your site here independant of the title.'),
        _('A total of ${number} pages are affected.',
          mapping={'number': subpage_count})
    ]

    if form.submitted(request):
        migration = PageNameChange.from_form(self.page, form)
        link_count = migration.execute(test=form.test.data)
        if not form.test.data:
            request.success(_("Your changes were saved"))
            return morepath.redirect(request.link(self.page))
        else:
            transaction.abort()

        messages.append(
            _('${count} links will be replaced by this action.',
              mapping={'count': link_count}))

    elif not request.POST:
        form.process(obj=self.page)

    site_title = _('Change Url')

    return {
        'layout': layout or EditorLayout(self, request, site_title),
        'form': form,
        'title': site_title,
        'callout': " ".join(request.translate(m) for m in messages)
    }
