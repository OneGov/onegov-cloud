""" Implements the adding/editing/removing of pages. """

import morepath

from onegov.core.security import Private
from onegov.page import PageCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.layout import EditorLayout
from onegov.town.models import Editor


def get_form_class(editor, request):
    return editor.page.get_form_class(editor.trait, request)


@TownApp.form(model=Editor, template='form.pt', permission=Private,
              form=get_form_class)
def handle_page_form(self, request, form):
    if self.action == 'new':
        return handle_new_page(self, request, form)
    elif self.action == 'edit':
        return handle_edit_page(self, request, form)
    else:
        raise NotImplementedError


def handle_new_page(self, request, form):

    if form.submitted(request):
        pages = PageCollection(request.app.session())
        page = pages.add(
            parent=self.page,
            title=form.title.data,
            type=self.page.type,
            meta={'trait': self.trait}
        )
        form.update_model(page)

        request.success(page.trait_messages[page.trait]['new_page_added'])
        return morepath.redirect(request.link(page))

    site_title = self.page.trait_messages[self.trait]['new_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_edit_page(self, request, form):
    if form.submitted(request):
        form.update_model(self.page)
        request.success(_(u"Your changes were saved"))

        return morepath.redirect(request.link(self.page))
    else:
        form.apply_model(self.page)

    site_title = self.page.trait_messages[self.trait]['edit_page_title']

    return {
        'layout': EditorLayout(self, request, site_title),
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }
