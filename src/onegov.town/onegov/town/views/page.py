""" Renders a onegov.page. """

import morepath

from onegov.core.security import Public, Private
from onegov.page import Page, PageCollection
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import DeleteLink, Link, LinkGroup
from onegov.town.layout import NewsLayout, PageLayout
from onegov.town.models import Editor
from webob import exc


@TownApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    PageCollection(request.app.session()).delete(self)
    request.success(self.trait_messages[self.trait]['delete_message'])


@TownApp.html(model=Page, template='page.pt', permission=Public)
def view_topic(self, request):
    if not request.is_logged_in:
        return view_public_page(self, request)
    else:
        return view_private_page(self, request)


def view_public_page(self, request):

    if self.trait == 'link':
        return morepath.redirect(self.content['url'])

    if self.trait == 'page':
        return {
            'layout': PageLayout(self, request),
            'title': self.title,
            'name': self.trait_messages[self.trait]['name'],
            'page': self,
            'children': [
                Link(child.title, request.link(child), model=child)
                for child in sorted(
                    request.exclude_invisible(self.children),
                    key=lambda c: c.name
                )
            ]
        }

    if self.trait == 'news':
        return {
            'layout': NewsLayout(self, request),
            'title': self.title,
            'name': self.trait_messages[self.trait]['name'],
            'page': self,
            'children': request.exclude_invisible(self.news_query.all()),
        }

    raise NotImplementedError


def view_private_page(self, request):

    editbar_links = [
        LinkGroup(
            title=self.trait_messages[self.trait]['name'],
            links=tuple(edit_links(self, request))
        ),
        LinkGroup(
            title=_(u'Add'),
            links=tuple(add_links(self, request))
        ),
    ]

    if self.type == 'topic':
        layout = PageLayout(self, request)
        layout.editbar_links = editbar_links

        return {
            'layout': layout,
            'title': self.title,
            'name': self.trait_messages[self.trait]['name'],
            'page': self,
            'children': [
                Link(child.title, request.link(child), model=child)
                for child in self.children
            ]
        }

    if self.type == 'news':
        layout = NewsLayout(self, request)
        layout.editbar_links = editbar_links

        return {
            'layout': layout,
            'title': self.title,
            'name': self.trait_messages[self.trait]['name'],
            'page': self,
            'children': self.news_query.all()
        }


def add_links(self, request):
    for trait in self.allowed_subtraits:

        name = self.trait_messages[trait]['name']

        yield Link(
            name,
            request.link(Editor('new', self, trait)),
            classes=('new-{}'.format(trait), 'show-new-content-placeholder')
        )


def edit_links(self, request):
    if self.editable:
        yield Link(
            _("Edit"),
            request.link(Editor('edit', self)),
            classes=('edit-{}'.format(self.trait), )
        )

    if self.deletable:
        trait_messages = self.trait_messages[self.trait]

        if self.children:
            extra_warning = _(
                "Please note that this page has subpages "
                "which will also be deleted!"
            )
        else:
            extra_warning = ""

        yield DeleteLink(
            _("Delete"), request.link(self),
            confirm=_(trait_messages['delete_question'], mapping={
                'title': self.title
            }),
            yes_button_text=trait_messages['delete_button'],
            extra_information=extra_warning,
            redirect_after=request.link(self.parent)
        )
