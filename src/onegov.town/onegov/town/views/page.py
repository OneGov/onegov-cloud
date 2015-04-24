""" Renders a onegov.page. """

import morepath

from onegov.core.security import Public, Private
from onegov.page import Page, PageCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import PageLayout
from onegov.town.model import LinkEditor, PageEditor


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
        'add_links': tuple(get_links(self, request, 'add')),
        'edit_links': tuple(get_links(self, request, 'edit')),
        'children': [
            Link(child.title, request.link(child)) for child in self.children
        ]
    }


@TownApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if self.meta['type'] == 'page':
        message = _(u"The page was deleted")
    else:
        message = _(u"The link was deleted")

    PageCollection(request.app.session()).delete(self)
    request.success(message)


def get_links(self, request, action):

    if self.meta['type'] in ('town-root', 'page') and action == 'add':
        yield Link(
            _("Page"), request.link(PageEditor('new', self)),
            classes=('new-page', )
        )

        yield Link(
            _("Link"), request.link(LinkEditor('new', self)),
            classes=('new-link', )
        )

    if self.meta['type'] == 'town-root' and action == 'edit':
        yield Link(
            _("Edit"), request.link(PageEditor('edit', self)),
            classes=('edit-page', )
        )

    if self.meta['type'] == 'page' and action == 'edit':
        yield Link(
            _("Edit"), request.link(PageEditor('edit', self)),
            classes=('edit-page', )
        )

        if self.children:
            extra_warning = _(
                "Please note that this page has subpages "
                "which will also be deleted!"
            )
        else:
            extra_warning = ""

        yield Link(
            _("Delete"), request.link(self), request_method='DELETE',
            classes=('confirm', 'delete-page'),
            attributes={
                'data-confirm': _(
                    "Do you really want to delete the page \"${title}\"?",
                    mapping={
                        'title': self.title
                    }
                ),
                'data-confirm-yes': _("Delete Page"),
                'data-confirm-no': _("Cancel"),
                'data-confirm-extra': extra_warning,
                'redirect-after': request.link(self.parent)
            },
        )

    if self.meta['type'] == 'link' and action == 'edit':
        yield Link(
            _("Edit"), request.link(LinkEditor('edit', self)),
            classes=('edit-link', )
        )
        yield Link(
            _("Delete"), request.link(self), request_method='DELETE',
            classes=('confirm', 'delete-link'),
            attributes={
                'data-confirm': _(
                    "Do you really want to delete the link \"${title}\"?",
                    mapping={
                        'title': self.title
                    }
                ),
                'data-confirm-yes': _("Delete Link"),
                'data-confirm-no': _("Cancel"),
                'redirect-after': request.link(self.parent)
            }
        )
