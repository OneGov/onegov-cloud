""" Renders a onegov.page. """
from __future__ import annotations

import morepath
from markupsafe import Markup

from feedgen.ext.base import BaseExtension  # type:ignore[import-untyped]
from feedgen.feed import FeedGenerator  # type:ignore[import-untyped]
from feedgen.util import xml_elem  # type:ignore[import-untyped]
from onegov.core.elements import Link as CoreLink
from onegov.core.security import Public, Private
from onegov.core.utils import append_query_param
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.homepage_widgets import get_lead
from onegov.org.layout import PageLayout, NewsLayout
from onegov.org.models import News, NewsCollection, Topic
from onegov.org.models.editor import Editor
from onegov.page import PageCollection
from webob import exc, Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from lxml.etree import _Element
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.view(model=Topic, request_method='DELETE', permission=Private)
@OrgApp.view(model=News, request_method='DELETE', permission=Private)
def delete_page(self: Topic | News, request: OrgRequest) -> None:
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
    request: OrgRequest,
    layout: PageLayout | None = None
) -> RenderData | Response:

    assert self.trait in {'link', 'page', 'iframe'}

    if not request.is_manager:

        if not self.published:
            return exc.HTTPNotFound()

        if self.trait == 'link':
            return morepath.redirect(self.content['url'])

    layout = layout or PageLayout(self, request)
    if self.photo_album_id:
        request.include('photoswipe')

    if request.is_manager:
        layout.editbar_links = self.get_editbar_links(request)
        if not isinstance(layout.editbar_links, list):
            # just a bit of safety since get_editbar_links doesn't
            # have to return a list
            layout.editbar_links = list(layout.editbar_links)

        layout.editbar_links.insert(
            len(layout.editbar_links) - 1,
            Link(
                _('Sort'),
                request.link(Editor('sort', self)),
                classes=('sort-link', )
            )
        )
        layout.editbar_links.insert(
            len(layout.editbar_links) - 1,
            Link(
                _('Move'),
                request.link(Editor('move', self)),
                classes=('move-link', )
            )
        )
        children = self.children
    else:
        children = request.exclude_invisible(
            c for c in self.children if c.published
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
        'iframe': self.content['url'] if self.trait == 'link' else None
    }


@OrgApp.html(model=NewsCollection, template='news.pt', permission=Public)
def view_news_collection(
    self: NewsCollection,
    request: OrgRequest,
    layout: NewsLayout | None = None
) -> RenderData | Response:

    if self.root is None:
        raise exc.HTTPNotFound()

    children: Sequence[News] = self.batch
    if not request.is_manager:
        # we should have pre-emptively excluded anything that
        # should be hidden, but let's do it again anyway to be safe
        children = request.exclude_invisible(self.batch)

    if request.params.get('format', '') == 'rss':
        def get_description(item: News) -> str:
            description = item.content.get('lead', '')
            if item.page_image and item.show_preview_image:
                description += str(
                    Markup(
                        '<p><img style="margin-right:10px;margin-bottom:10px;'
                        'width:300px;height:auto;" src="{}"></p>'
                    ).format(item.page_image)
                )
            return description

        next_page = self.next
        prev_page = self.previous
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
            prev_url=request.link(
                prev_page,
                query_params={'format': 'rss'}
            ) if prev_page else None,
            next_url=request.link(
                next_page,
                query_params={'format': 'rss'}
            ) if next_page else None,
            feed_title=request.domain + ' News',
            language=request.app.org.meta['locales'],
        )
        return Response(
            rss_str,
            content_type='application/rss+xml ',
            content_disposition='inline; filename=news.rss'
        )

    rss_link_for_selected_tags = (
        append_query_param(request.url, 'format', 'rss')
    )

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

    layout = layout or NewsLayout(self.root, request)

    if request.is_manager:
        layout.editbar_links = list(self.root.get_editbar_links(request))
    if self.root.photo_album_id:
        request.include('photoswipe')

    assert self.root.trait is not None
    return {
        'layout': layout,
        'title': self.root.title,
        'name': self.root.trait_messages[self.root.trait]['name'],
        'page': self.root,
        'pagination': self,
        'children': children,
        'rss_link': rss_link_for_selected_tags,
        'year_links': year_links,
        'tag_links': tag_links,
        'get_lead': get_lead,
        'siblings': []
    }


@OrgApp.html(model=News, template='news.pt', permission=Public)
def view_news(
    self: News,
    request: OrgRequest,
    layout: NewsLayout | None = None
) -> RenderData | Response:

    assert isinstance(self.parent, News)
    news = NewsCollection(request)
    query = news.subset().filter(News.id != self.id).limit(3)
    if request.is_manager:
        siblings = query.all()
    else:
        # we should have pre-emptively excluded anything that
        # should be hidden, but let's do it again anyway to be safe
        siblings = request.exclude_invisible(query)

    layout = layout or NewsLayout(self, request)
    if request.is_manager:
        layout.editbar_links = list(self.get_editbar_links(request))
    if self.photo_album_id:
        request.include('photoswipe')

    assert self.trait is not None
    return {
        'layout': layout,
        'title': self.title,
        'name': self.trait_messages[self.trait]['name'],
        'page': self,
        'pagination': None,
        'children': [],
        'rss_link': None,
        'year_links': [],
        'tag_links': [],
        'get_lead': get_lead,
        'siblings': siblings
    }


class AtomLinkInRSSExtension(BaseExtension):  # type: ignore[misc]

    def __init__(self) -> None:
        self.fg = FeedGenerator()

    def extend_rss(self, feed: _Element) -> _Element:
        for link in reversed(self.fg.link()):
            # insert in the channel after the generic link element
            feed[0].insert(2, xml_elem(
                '{http://www.w3.org/2005/Atom}link',
                href=link['href'],
                rel=link['rel']
            ))
        return feed

    def link(self, href: str, rel: str) -> None:
        self.fg.link(href=href, rel=rel)


def generate_rss_feed(
    items: list[dict[str, str | datetime]],
    request_url: str,
    prev_url: str | None,
    next_url: str | None,
    feed_title: str,
    language: str = 'de_CH'
) -> str:

    fg = FeedGenerator()
    fg.register_extension('atom', AtomLinkInRSSExtension, atom=False)
    fg.id(request_url)
    fg.title(feed_title)
    fg.description(feed_title)
    fg.language(language)
    fg.link(href=request_url)
    fg.atom.link(href=request_url, rel='alternate')
    if prev_url is not None:
        fg.atom.link(href=prev_url, rel='previous')
    if next_url is not None:
        fg.atom.link(href=next_url, rel='next')

    for item in items:
        feed_entry = fg.add_entry()
        feed_entry.id(item.get('id', '#'))
        feed_entry.description(item.get('description'), isSummary=True)
        feed_entry.title(item.get('title', 'No Title'))
        feed_entry.link(href=item.get('link', '#'))
        if published_date := item.get('published'):
            feed_entry.published(published_date)

    return fg.rss_str(pretty=True)
