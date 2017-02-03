""" Renders a onegov.page. """

import morepath

from datetime import datetime
from onegov.core.security import Public, Private
from onegov.org.elements import Link
from onegov.org.layout import PageLayout, NewsLayout
from onegov.org.models import News, Topic
from onegov.page import Page, PageCollection
from onegov.org import OrgApp
from sedate import replace_timezone
from webob import exc


@OrgApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    PageCollection(request.app.session()).delete(self)
    request.success(self.trait_messages[self.trait]['delete_message'])


@OrgApp.html(model=Topic, template='topic.pt', permission=Public)
def view_topic(self, request):

    assert self.trait in {'link', 'page'}

    if not request.is_manager and self.trait == 'link':
        return morepath.redirect(self.content['url'])

    layout = PageLayout(self, request)

    if request.is_manager:
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
            for child in children
        ]
    }


@OrgApp.html(model=News, template='news.pt', permission=Public)
def view_news(self, request):

    layout = NewsLayout(self, request)
    years = self.years

    try:
        year = int(request.params['year'])
    except (ValueError, KeyError):
        year = years and years[0] or None

    query = self.news_query(limit=None)

    if year:
        start = replace_timezone(datetime(year, 1, 1), 'UTC')
        query = query.filter(Page.created >= start)
        query = query.filter(Page.created < start.replace(year=year + 1))

    if request.is_manager:
        layout.editbar_links = list(self.get_editbar_links(request))
        children = query.all()
    else:
        children = request.exclude_invisible(query.all())

    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': children,
        'years': years,
        'current_year': year
    }
