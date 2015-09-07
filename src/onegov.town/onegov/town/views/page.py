""" Renders a onegov.page. """

import morepath

from onegov.core.security import Public, Private
from onegov.page import Page, PageCollection
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import PageLayout, NewsLayout
from onegov.town.models import News, Topic
from webob import exc


@TownApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    PageCollection(request.app.session()).delete(self)
    request.success(self.trait_messages[self.trait]['delete_message'])


@TownApp.html(model=Topic, template='page.pt', permission=Public)
def view_topic(self, request):

    assert self.trait in {'link', 'page'}

    if not request.is_logged_in and self.trait == 'link':
        return morepath.redirect(self.content['url'])

    layout = PageLayout(self, request)

    if request.is_logged_in:
        layout.editbar_links = self.get_editbar_links(request)
        children = self.children
    else:
        children = request.exclude_invisible(self.children)

    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': [
            Link(child.title, request.link(child), model=child)
            for child in sorted(children, key=lambda c: c.title)
        ]
    }


@TownApp.html(model=News, template='page.pt', permission=Public)
def view_news(self, request):

    layout = NewsLayout(self, request)

    if request.is_logged_in:
        layout.editbar_links = list(self.get_editbar_links(request))
        children = self.news_query.all()
    else:
        children = request.exclude_invisible(self.news_query.all())

    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': children,
    }
