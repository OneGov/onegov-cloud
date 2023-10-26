""" Renders a onegov.page. """

import morepath

from onegov.core.elements import Link as CoreLink
from onegov.core.security import Public, Private
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.homepage_widgets import get_lead
from onegov.org.layout import PageLayout, NewsLayout
from onegov.org.models import News, Topic
from onegov.org.models.editor import Editor
from onegov.page import Page, PageCollection
from webob import exc
from webob.exc import HTTPNotFound


@OrgApp.view(model=Page, request_method='DELETE', permission=Private)
def delete_page(self, request):
    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    # first remove all the linked files
    self.files = []
    request.session.flush()

    PageCollection(request.session).delete(self)
    request.success(self.trait_messages[self.trait]['delete_message'])


@OrgApp.html(model=Topic, template='topic.pt', permission=Public)
def view_topic(self, request, layout=None):

    assert self.trait in {'link', 'page'}

    if not request.is_manager:

        if not self.published:
            return HTTPNotFound()

        if self.trait == 'link':
            return morepath.redirect(self.content['url'])

    layout = layout or PageLayout(self, request)

    if request.is_manager:
        layout.editbar_links = self.get_editbar_links(request)
        layout.editbar_links.insert(
            len(layout.editbar_links) - 1,
            Link(
                _("Sort"),
                request.link(Editor('sort', self)),
                classes=('sort-link', )
            )
        )
        layout.editbar_links.insert(
            len(layout.editbar_links) - 1,
            Link(
                _("Move"),
                request.link(Editor('move', self)),
                classes=('move-link', )
            )
        )
        children = self.children
    else:
        children = request.exclude_invisible(
            (c for c in self.children if c.published)
        )

    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': [
            (
                child.lead_when_child and child.lead,
                child.title,
                Link(child.title, request.link(child), model=child),
                child.content['url'] if child.trait == 'link' else
                request.link(child),
                request.link(
                    Editor('edit', child)) if child.trait == 'link' else None,
                child.page_image,
                child.show_preview_image
            )
            for child in children
        ],
        'children_images': any(child.page_image for child in children)
    }


@OrgApp.html(model=News, template='news.pt', permission=Public)
def view_news(self, request, layout=None):

    layout = layout or NewsLayout(self, request)

    children = []
    year_links = []
    tag_links = []
    siblings = []
    if not self.parent:
        query = self.news_query(limit=None)
        if request.is_manager:
            children = query.all()
        else:
            children = request.exclude_invisible(query.all())

        year_links = [CoreLink(
            text=str(year),
            active=year in self.filter_years,
            url=request.link(self.for_year(year)),
            rounded=True
        ) for year in self.all_years]

        tag_links = [CoreLink(
            text=str(tag),
            active=tag in self.filter_tags,
            url=request.link(self.for_tag(tag)),
            rounded=True
        ) for tag in self.all_tags]
    else:
        query = self.parent.news_query(limit=None)
        if request.is_manager:
            siblings = query.all()
        else:
            siblings = request.exclude_invisible(query.all())

        if self in siblings:
            siblings.remove(self)
        siblings = siblings[0:3]

    if request.is_manager:
        layout.editbar_links = list(self.get_editbar_links(request))

    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': children,
        'year_links': year_links,
        'tag_links': tag_links,
        'get_lead': get_lead,
        'siblings': siblings
    }
