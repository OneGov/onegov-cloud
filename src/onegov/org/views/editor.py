""" Implements the adding/editing/removing of pages. """

import morepath
from webob.exc import HTTPForbidden

from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.forms.page import MovePageForm, PageUrlForm
from onegov.org.layout import EditorLayout, PageLayout
from onegov.org.management import PageNameChange
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
    if editor.action == 'move':
        return MovePageForm
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
    elif self.action == 'sort':
        return morepath.redirect(request.link(self, 'sort'))
    elif self.action == 'move':
        return handle_move_page(self, request, form, layout=layout)
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

    layout = layout or EditorLayout(self, request, site_title)
    layout.site_title = site_title

    if self.page.deletable and self.page.trait == "link":
        edit_links = self.page.get_edit_links(request)
        layout.editbar_links = filter(
            lambda link: link.text == _("Delete"), edit_links
        )

    if form.submitted(request):
        form.populate_obj(self.page)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self.page))
    elif not request.POST:
        form.process(obj=self.page)

    return {
        'layout': layout,
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_move_page(self, request, form, layout=None):
    layout = layout or PageLayout(self.page, request)
    layout.site_title = self.page.trait_messages[self.trait]['move_page_title']

    if form.submitted(request):
        form.update_model(self.page)
        request.success(_("Your changes were saved"))

        return morepath.redirect(request.link(self.page))

    return {
        'layout': layout,
        'title': layout.site_title,
        'helptext': _("Moves the topic and all its sub topics to the "
                      "given destination."),
        'form': form,
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
        _('Stable URLs are important. Here you can change the '
          'path to your site independently from the title.'),
        _('A total of ${number} subpages are affected.',
          mapping={'number': subpage_count})
    ]

    if form.submitted(request):
        migration = PageNameChange.from_form(self.page, form)
        link_count = migration.execute(test=form.test.data)
        if not form.test.data:
            request.app.cache.delete(
                f'{request.app.application_id}.root_pages'
            )
            request.success(_("Your changes were saved"))

            @request.after
            def must_revalidate(response):
                response.headers.add('cache-control', 'must-revalidate')
                response.headers.add('cache-control', 'max-age=0, public')
                response.headers['expires'] = '0'

            return morepath.redirect(request.link(self.page))

        messages.append(
            _('${count} links will be replaced by this action.',
              mapping={'count': link_count}))

    elif not request.POST:
        form.process(obj=self.page)

    site_title = _('Change URL')

    return {
        'layout': layout or EditorLayout(self, request, site_title),
        'form': form,
        'title': site_title,
        'callout': " ".join(request.translate(m) for m in messages)
    }


@OrgApp.html(
    model=Editor,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_topics_sort(self, request, layout=None):
    layout = layout or EditorLayout(self, request, 'sort')

    return {
        'title': _("Sort"),
        'layout': layout,
        'page': self.page,
        'pages': self.page.children
    }
