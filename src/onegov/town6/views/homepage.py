from __future__ import annotations

from urllib.parse import urlsplit

from onegov.core.security import Public, Private
from onegov.org.views.homepage import view_org
from onegov.org.models import Organisation
from onegov.chat.collections import ChatCollection
from onegov.page import Page, PageCollection
from onegov.town6 import _, TownApp
from onegov.town6.layout import HomepageLayout
from webob import Response


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.org.request import PageMeta
    from onegov.town6.request import TownRequest


@TownApp.html(model=Organisation, template='homepage.pt', permission=Public)
def town_view_org(
    self: Organisation,
    request: TownRequest
) -> RenderData | Response:
    view = view_org(self, request, HomepageLayout(self, request))
    # catch redirect
    if isinstance(view, Response):
        return view
    if self.enable_chat == 'people_chat':
        chats = ChatCollection(request.session)
        chat_link = request.link(chats, 'initiate')
    else:
        chat_link = self.chat_link if self.chat_link else '#'
    view['chat_link'] = chat_link

    return view


@TownApp.html(
    model=Organisation,
    template='sort.pt',
    name='sort',
    permission=Private
)
def view_pages_sort(
    self: Organisation,
    request: TownRequest,
    layout: HomepageLayout | None = None
) -> RenderData:
    layout = layout or HomepageLayout(self, request)

    return {
        'title': _('Sort'),
        'layout': layout,
        'page': self,
        'pages': layout.root_pages
    }


@TownApp.html(
    model=Organisation,
    template='information_architecture.pt',
    name='information-architecture',
    permission=Private
)
def view_information_architecture(
    self: Organisation,
    request: TownRequest
) -> RenderData:
    request.include('information-architecture')

    return {
        'title': _('Information Architecture'),
        'layout': HomepageLayout(self, request),
        'data_url': request.link(
            self, name='information-architecture-data'
        )
    }


@TownApp.json(
    model=Organisation,
    name='information-architecture-data',
    permission=Private,
    open_data=False
)
def view_information_architecture_data(
    self: Organisation,
    request: TownRequest
) -> RenderData:
    def iter_page_ids(pages: tuple[PageMeta, ...]) -> Iterator[int]:
        for page in pages:
            yield page.id
            yield from iter_page_ids(page.children)

    def clean_lead(value: str | None) -> str:
        return ' '.join(value.split()) if value else ''

    page_tree = request.pages_tree
    page_ids = tuple(iter_page_ids(page_tree))
    page_collection = PageCollection(request.session)
    lead_expression = Page.content['lead'].as_string()
    page_leads = {
        page_id: clean_lead(lead)
        for page_id, lead in request.session.query(
            Page.id, lead_expression
        ).filter(Page.id.in_(page_ids))
    }

    def to_node(page: PageMeta) -> dict[str, Any]:
        url = page.link(request)
        return {
            'id': f'page-{page.id}',
            'title': page.title,
            'lead': page_leads.get(page.id, ''),
            'path': urlsplit(url).path,
            'url': url,
            'kind': page.type,
            'access': page.access,
            'published': page.published,
            'children': [to_node(child) for child in page.children]
        }

    def to_route_node(
        name: str,
        path: str,
        children: list[dict[str, Any]],
        backing_page: PageMeta | None = None
    ) -> dict[str, Any]:
        return {
            'id': f'route-{name}',
            'title': path,
            'lead': (
                page_leads.get(backing_page.id, '')
                if backing_page else ''
            ),
            'path': path,
            'url': backing_page.link(request) if backing_page else None,
            'kind': 'route',
            'page_kind': backing_page.type if backing_page else None,
            'backing_page_id': backing_page.id if backing_page else None,
            'access': backing_page.access if backing_page else 'public',
            'published': backing_page.published if backing_page else True,
            'children': children
        }

    def count_pages(pages: tuple[PageMeta, ...]) -> int:
        return sum(
            1 + count_pages(page.children)
            for page in pages
        )

    topic_pages: list[PageMeta] = []
    news_pages: list[PageMeta] = []
    pages = []
    for page in page_tree:
        if page.type == 'topic':
            topic_pages.append(page)
        elif page.type == 'news':
            news_pages.append(page)
        else:
            pages.append(to_node(page))

    homepage_url = request.link(self)
    homepage_path = urlsplit(homepage_url).path.rstrip('/')
    if topic_pages:
        pages.append(to_route_node(
            'topics',
            f'{homepage_path}/topics',
            [to_node(page) for page in topic_pages]
        ))

    news_root = page_collection.by_path('/news/', ensure_type='news')
    news_root = news_root or page_collection.by_path(
        '/aktuelles/', ensure_type='news'
    )
    news_root_meta = next(
        (
            page for page in news_pages
            if page.id == getattr(news_root, 'id', None)
        ),
        None
    )
    if news_root_meta:
        pages.append(to_route_node(
            'news',
            f'{homepage_path}/news',
            [to_node(child) for child in news_root_meta.children],
            backing_page=news_root_meta
        ))
    pages.extend(
        to_node(page)
        for page in news_pages
        if page is not news_root_meta
    )

    page_count = count_pages(page_tree)
    translate = request.translate

    return {
        'tree': {
            'id': 'homepage',
            'title': self.title,
            'lead': clean_lead(self.og_description),
            'path': urlsplit(homepage_url).path or '/',
            'url': homepage_url,
            'kind': 'homepage',
            'access': 'public',
            'published': True,
            'children': pages
        },
        'summary': translate(
            _('${count} pages', mapping={'count': page_count})
        ),
        'labels': {
            'homepage': translate(_('Homepage')),
            'route': translate(_('URL path')),
            'topic': translate(_('Topic')),
            'news': translate(_('News')),
            'unpublished': translate(_('Unpublished')),
            'restricted': translate(_('Restricted')),
            'open_page': translate(_('Open page')),
            'expand_branch': translate(_('Expand branch')),
            'collapse_branch': translate(_('Collapse branch')),
            'export_image': translate(_('Export as image')),
            'exporting_image': translate(_('Exporting image…')),
            'export_error': translate(_('The image could not be exported.')),
            'search': translate(_('Search')),
            'clear_search': translate(_('Clear search')),
            'search_results': translate(_('Search results')),
            'vertical': translate(_('Top to bottom')),
            'horizontal': translate(_('Left to right')),
            'loading': translate(_('Arranging URL hierarchy…')),
            'error': translate(_('The URL hierarchy could not be loaded.'))
        }
    }
