""" Renders a onegov.page. """

import morepath
from markupsafe import Markup

from onegov.core.elements import Link as CoreLink
from onegov.core.security import Public, Private
from onegov.core.utils import append_query_param
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.homepage_widgets import get_lead
from onegov.org.layout import PageLayout, NewsLayout
from onegov.org.models import News, Topic
from onegov.org.models.editor import Editor
from onegov.page import PageCollection
from webob import exc
from webob.exc import HTTPNotFound
from feedgen.feed import FeedGenerator  # type:ignore[import-untyped]
from webob import Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.view(model=Topic, request_method='DELETE', permission=Private)
@OrgApp.view(model=News, request_method='DELETE', permission=Private)
def delete_page(self: Topic | News, request: 'OrgRequest') -> None:
    request.assert_valid_csrf_token()

    if not self.deletable:
        raise exc.HTTPMethodNotAllowed()

    # first remove all the linked files
    self.files = []
    request.session.flush()

    PageCollection(request.session).delete(self)
    assert self.trait is not None
    request.success(self.trait_messages[self.trait]['delete_message'])


@OrgApp.html(model=Topic, template='topic.pt', permission=Public)
def view_topic(
    self: Topic,
    request: 'OrgRequest',
    layout: PageLayout | None = None
) -> 'RenderData | Response':

    assert self.trait in {'link', 'page', 'iframe'}

    if not request.is_manager:

        if not self.published:
            return HTTPNotFound()

        if self.trait == 'link':
            return morepath.redirect(self.content['url'])

    layout = layout or PageLayout(self, request)

    if request.is_manager:
        layout.editbar_links = self.get_editbar_links(request)
        if not isinstance(layout.editbar_links, list):
            # just a bit of safety since get_editbar_links doesn't
            # have to return a list
            layout.editbar_links = list(layout.editbar_links)

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
                child.lead if child.lead_when_child else None,
                child.title,
                Link(child.title, request.link(child), model=child),
                child.content['url'] if child.trait == 'link' else
                request.link(child),
                request.link(
                    Editor('edit', child)
                ) if child.trait == 'link' else None,
                child.page_image,
                child.show_preview_image
            )
            for child in children
            if isinstance(child, Topic)
        ],
        'children_images': any(
            isinstance(child, Topic)
            and child.page_image
            and child.show_preview_image
            for child in children
        ),
    }


@OrgApp.html(model=News, template='news.pt', permission=Public)
def view_news(
    self: News,
    request: 'OrgRequest',
    layout: NewsLayout | None = None
) -> 'RenderData | Response':

    layout = layout or NewsLayout(self, request)

    children = []
    year_links = []
    tag_links = []
    rss_link_for_selected_tags = None
    siblings = []
    if not self.parent:
        if request.is_manager:
            query = self.news_query(limit=None, published_only=False)
            children = query.all()
        else:
            query = self.news_query(limit=None)
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

        url = request.url
        if 'format' in url:
            rss_link_for_selected_tags = url
        else:
            rss_link_for_selected_tags = (
                append_query_param(url, 'format', 'rss')
                if self.filter_tags else None
            )
    else:
        assert isinstance(self.parent, News)
        query = self.parent.news_query(limit=None)
        if request.is_manager:
            siblings = query.all()
        else:
            siblings = request.exclude_invisible(query.all())

        if self in siblings:
            siblings.remove(self)
        siblings = siblings[0:3]

    if request.params.get('format', '') == 'rss':
        def get_description(item: News) -> str:
            description = item.content.get('lead', "")
            if item.page_image and item.show_preview_image:
                description += str(
                    Markup(
                        '<p><img style="margin-right:10px;margin-bottom:10px;'
                        'width:300px;height:auto;" src="{}"></p>'
                    ).format(item.page_image)
                )
            return description

        rss_str = generate_rss_feed(
            [
                {
                    'id': news.name,
                    'title': news.title,
                    'link': request.link(news),
                    'description': get_description(news),
                    'published': news.published_or_created
                }
                for news in children
            ],
            request_url=request.link(self),
            feed_title=request.domain + ' News',
            language=request.app.org.meta['locales'],
        )
        return Response(
            rss_str,
            content_type='application/rss+xml ',
            content_disposition=f'inline; filename={self.name}.rss'
        )

    if request.is_manager:
        layout.editbar_links = list(self.get_editbar_links(request))

    assert self.trait is not None
    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'children': children,
        'rss_link': rss_link_for_selected_tags,
        'year_links': year_links,
        'tag_links': tag_links,
        'get_lead': get_lead,
        'siblings': siblings
    }


def generate_rss_feed(
    items: list[dict[str, str | bool]],
    request_url: str,
    feed_title: str,
    language: str = "de_CH"
) -> str:

    fg = FeedGenerator()
    fg.id(request_url)
    fg.title(feed_title)
    fg.description(feed_title)
    fg.language(language)
    fg.link(href=request_url, rel='alternate')

    for item in items:
        feed_entry = fg.add_entry()
        feed_entry.id(item.get('id', '#'))
        feed_entry.description(item.get('description'), isSummary=True)
        feed_entry.title(item.get('title', 'No Title'))
        feed_entry.link(href=item.get('link', '#'))
        if published_date := item.get('published'):
            feed_entry.published(published_date)

    return fg.rss_str(pretty=True)
