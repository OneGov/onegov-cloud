""" Implements the adding/editing/removing of pages. """
from __future__ import annotations

import morepath
from webob.exc import HTTPForbidden, HTTPNotFound

from onegov.core.elements import BackLink, Link
from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org.forms.page import MovePageForm, PageUrlForm, PageForm
from onegov.org.layout import EditorLayout, PageLayout
from onegov.org.management import PageNameChange
from onegov.org.models import Clipboard, Editor
from onegov.org.models.organisation import Organisation
from onegov.org.models import News
from onegov.page import PageCollection


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.models import Topic
    from onegov.org.request import OrgRequest
    from onegov.page import Page
    from webob import Response


def get_form_class(
    editor: Editor,
    request: OrgRequest
) -> type[Form]:

    src = Clipboard.from_session(request).get_object()

    if src and editor.action == 'paste':
        assert editor.page is not None
        if src and src.trait in editor.page.allowed_subtraits:
            return editor.page.get_form_class(
                src.trait, editor.action, request)
    if editor.action == 'change-url':
        return PageUrlForm
    if editor.action == 'move':
        return MovePageForm
    if editor.action == 'new-root':
        # this is the case when adding a new 'root' page (parent = None)
        return PageForm

    assert editor.page is not None
    return editor.page.get_form_class(editor.trait, editor.action, request)


@OrgApp.form(model=Editor, template='form.pt', permission=Private,
             form=get_form_class)
def handle_page_form(
    self: Editor,
    request: OrgRequest,
    form: Form,
    # FIXME: This is really bad, they should all use the same layout
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:
    if self.action == 'new':
        return handle_new_page(self, request, form, layout=layout)
    if self.action == 'new-root':
        return handle_new_root_page(self, request, form, layout=layout)
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


def handle_new_page(
    self: Editor,
    request: OrgRequest,
    form: Form,
    src: object | None = None,
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:
    assert self.page is not None
    page = cast('Topic | News', self.page)
    site_title = page.trait_messages[self.trait]['new_page_title']

    if layout:
        layout.site_title = site_title  # type:ignore[union-attr]

    if form.submitted(request):
        pages = PageCollection(request.session)
        added = cast('Topic | News', pages.add(
            parent=page,
            title=form['title'].data,
            type=page.type,
            meta={'trait': self.trait}
        ))
        form.populate_obj(added)

        request.success(added.trait_messages[self.trait]['new_page_added'])
        return morepath.redirect(request.link(added))

    if src:
        form.process(obj=src)

    layout = layout or EditorLayout(self, request, site_title)
    layout.editmode_links[1] = Link(
        text=_('Cancel'),
        url=request.link(self.page),
        attrs={'class': 'cancel-link'}
    )

    return {
        'layout': layout,
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_new_root_page(
    self: Editor,
    request: OrgRequest,
    form: Form,
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:
    site_title = _('New Topic')

    if layout:
        layout.site_title = site_title  # type:ignore[union-attr]

    if form.submitted(request):
        pages = PageCollection(request.session)
        page = pages.add(
            parent=None,  # root page
            title=form['title'].data,
            type='topic',
            meta={'trait': 'page'},
        )
        form.populate_obj(page)

        request.success(_('Added a new topic'))
        return morepath.redirect(request.link(page))

    if not request.POST:
        form.process(obj=self.page)
    layout = layout or EditorLayout(self, request, site_title)
    layout.edit_mode = True
    layout.editmode_links[1] = Link(
        text=_('Cancel'),
        url=request.class_link(Organisation),
        attrs={'class': 'cancel-link'}
    )

    return {
        'layout': layout,
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_edit_page(
    self: Editor,
    request: OrgRequest,
    form: Form,
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:
    assert self.page is not None
    site_title = self.page.trait_messages[self.trait]['edit_page_title']

    layout = layout or EditorLayout(self, request, site_title)
    layout.site_title = site_title  # type:ignore[union-attr]
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})

    if self.page.deletable and self.page.trait == 'link':
        edit_links = self.page.get_edit_links(request)
        links = layout.editmode_links + list(filter(
            lambda link: getattr(link, 'text', '') == _('Delete'), edit_links
        ))
        layout.editmode_links = links

    if form.submitted(request):
        form.populate_obj(self.page)
        request.success(_('Your changes were saved'))

        return morepath.redirect(request.link(self.page))
    elif not request.POST:
        form.process(obj=self.page)
        if self.page.trait == 'news':
            assert isinstance(self.page, News)
            if self.page.push_notifications_were_sent_before():
                request.message(_(
                    'Notifications have already been sent for this news item. '
                    'A new notification will not be sent, even if the '
                    'publication date is changed.'
                ), 'info',
                )

    return {
        'layout': layout,
        'title': site_title,
        'form': form,
        'form_width': 'large'
    }


def handle_move_page(
    self: Editor,
    request: OrgRequest,
    form: Form,
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:

    assert self.page is not None
    layout = layout or PageLayout(self.page, request)
    site_title = self.page.trait_messages[self.trait]['move_page_title']
    layout.site_title = site_title  # type:ignore[union-attr]

    if form.submitted(request):
        form.update_model(self.page)  # type:ignore[attr-defined]
        request.success(_('Your changes were saved'))

        return morepath.redirect(request.link(self.page))

    return {
        'layout': layout,
        'title': site_title,
        'helptext': _('Moves the topic and all its sub topics to the '
                      'given destination.'),
        'form': form,
    }


def handle_change_page_url(
    self: Editor,
    request: OrgRequest,
    form: Form,
    layout: EditorLayout | PageLayout | None = None
) -> RenderData | Response:

    if not request.is_admin:
        return HTTPForbidden()

    assert self.page is not None
    page = cast('Topic | News', self.page)

    subpage_count = 0

    def count_page(page: Page) -> None:
        nonlocal subpage_count
        subpage_count += 1
        for child in page.children:
            count_page(child)

    for child in page.children:
        count_page(child)

    messages = [
        _('Stable URLs are important. Here you can change the '
          'path to your site independently from the title.'),
        _('A total of ${number} subpages are affected.',
          mapping={'number': subpage_count})
    ]

    if form.submitted(request):
        migration = PageNameChange.from_form(page, form)
        link_count = migration.execute(test=form['test'].data)
        if not form['test'].data:
            # FIXME: I am not sure this is actually necessary
            #        the execution of the migration should cause
            #        a change in the pages tables, which in turn
            #        will clear these caches. But I suppose it doesn't
            #        hurt to clear them twice...
            for prop_name in ('root_pages', 'pages_tree', 'homepage_pages'):
                prop = getattr(request.__class__, prop_name)
                for cache_key in prop.used_cache_keys:
                    request.app.cache.delete(cache_key)
            request.success(_('Your changes were saved'))

            @request.after
            def must_revalidate(response: Response) -> None:
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
        'callout': ' '.join(request.translate(m) for m in messages)
    }


@OrgApp.html(
    model=Editor,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_topics_sort(
    self: Editor,
    request: OrgRequest,
    layout: EditorLayout | None = None
) -> RenderData:

    if self.page is None:
        raise HTTPNotFound()

    page = cast('Topic | News', self.page)

    layout = layout or EditorLayout(self, request, 'sort')

    return {
        'title': _('Sort'),
        'layout': layout,
        'page': page,
        'pages': page.children
    }
