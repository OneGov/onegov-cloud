""" Implements the adding/editing/removing of pages. """

import morepath

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.layout import EditorLayout
from onegov.org.models import Clipboard, Editor
from onegov.page import PageCollection


def get_form_class(editor, request):

    src = Clipboard.from_session(request).get_object()

    if src and editor.action == 'paste':
        if src and src.trait in editor.page.allowed_subtraits:
            return editor.page.get_form_class(src.trait, request)

    return editor.page.get_form_class(editor.trait, request)


@OrgApp.form(model=Editor, template='form.pt', permission=Private,
             form=get_form_class)
def handle_page_form(self, request, form):
    if self.action == 'new':
        return handle_new_page(self, request, form)
    elif self.action == 'edit':
        return handle_edit_page(self, request, form)
    elif self.action == 'paste':
        clipboard = Clipboard.from_session(request)
        src = clipboard.get_object()
        clipboard.clear()

        return handle_new_page(self, request, form, src)
    else:
        raise NotImplementedError


def handle_new_page(self, request, form, src=None):

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

    site_title = self.page.trait_messages[self.trait]['new_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_edit_page(self, request, form):
    if form.submitted(request):
        form.populate_obj(self.page)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self.page))
    elif not request.POST:
        form.process(obj=self.page)

    site_title = self.page.trait_messages[self.trait]['edit_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }
