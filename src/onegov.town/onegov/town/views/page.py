""" Renders a onegov.page. """

import morepath

from onegov.core.security import Public
from onegov.page import Page
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.model import LinkEditor, PageEditor


@TownApp.html(model=Page, template='page.pt', permission=Public)
def view_page(self, request):

    if self.meta['type'] == 'link' and not request.is_logged_in:
        return morepath.redirect(self.content['url'])

    if self.meta['type'] == 'link':
        add_links = []
    else:
        add_links = [
            Link(_(u"Page"), request.link(PageEditor('new', self))),
            Link(_(u"Link"), request.link(LinkEditor('new', self)))
        ]

    if self.meta['type'] == 'town-root':
        edit_links = [
            Link(_(u"Edit"), request.link(PageEditor('edit', self))),
        ]
    elif self.meta['type'] == 'page':
        edit_links = [
            Link(_(u"Edit"), request.link(PageEditor('edit', self))),
            Link(_(u"Delete"), request.link(PageEditor('delete', self)))
        ]
    elif self.meta['type'] == 'link':
        edit_links = [
            Link(_(u"Edit"), request.link(LinkEditor('edit', self))),
            Link(_(u"Delete"), request.link(LinkEditor('delete', self)))
        ]
    else:
        raise NotImplementedError

    return {
        'layout': DefaultLayout(self, request),
        'title': self.title,
        'page': self,
        'add_links': add_links,
        'edit_links': edit_links,
        'children': [
            Link(child.title, request.link(child)) for child in self.children
        ]
    }
