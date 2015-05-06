""" Renders a onegov.page. """

import morepath

from onegov.core.security import Public, Private
from onegov.page import Page, PageCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import PageLayout
from onegov.town.models import Editor
from webob import exc


@TownApp.html(model=Page, template='page.pt', permission=Public)
def view_page(self, request):
    if not request.is_logged_in:
        return view_public_page(self, request)
    else:
        return view_private_page(self, request)


def view_public_page(self, request):
    if self.meta['type'] == 'link':
        return morepath.redirect(self.content['url'])
    else:
        return {
            'layout': PageLayout(self, request),
            'title': self.title,
            'page': self,
            'children': [
                Link(child.title, request.link(child))
                for child in self.children
            ]
        }


def view_private_page(self, request):
    return {
        'layout': PageLayout(self, request),
        'title': self.title,
        'page': self,
        'add_links': tuple(add_links(self, request)),
        'edit_links': tuple(edit_links(self, request)),
        'children': [
            Link(child.title, request.link(child)) for child in self.children
        ]
    }


@TownApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if not self.type_info.get('deletable'):
        raise exc.HTTPMethodNotAllowed()

    PageCollection(request.app.session()).delete(self)
    request.success(self.type_info['delete_message'])


def add_links(self, request):
    for page_type in (self.type_info.get('allowed_subtypes') or tuple()):

        type_info = self.type_info_map[page_type]

        yield Link(
            type_info['name'],
            request.link(Editor('new', self, page_type)),
            classes=('new-{}'.format(page_type), )
        )


def edit_links(self, request):
    yield Link(
        _("Edit"),
        request.link(Editor('edit', self)),
        classes=('edit-{}'.format(self.type), )
    )

    if self.type_info.get('deletable'):
        if self.children:
            extra_warning = _(
                "Please note that this page has subpages "
                "which will also be deleted!"
            )
        else:
            extra_warning = ""

        yield Link(
            _("Delete"), request.link(self), request_method='DELETE',
            classes=('confirm', 'delete-{}'.format(self.type)),
            attributes={
                'data-confirm': _(
                    self.type_info['delete_question'], mapping={
                        'title': self.title
                    }),
                'data-confirm-yes': self.type_info['delete_button'],
                'data-confirm-no': _("Cancel"),
                'data-confirm-extra': extra_warning,
                'redirect-after': request.link(self.parent)
            }
        )
