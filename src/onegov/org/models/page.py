from __future__ import annotations

from datetime import datetime
from onegov.core.collection import Pagination
from onegov.core.orm.mixins import (
    content_property, dict_markup_property, dict_property, meta_property)
from onegov.form import Form, move_fields
from onegov.org import _
from onegov.org.forms import LinkForm, PageForm, IframeForm
from onegov.org.models.atoz import AtoZ
from onegov.org.models.extensions import (
    ContactExtension, ContactHiddenOnPageExtension,
    PeopleShownOnMainPageExtension, ImageExtension,
    NewsletterExtension, PublicationExtension, DeletableContentExtension,
    InlinePhotoAlbumExtension, SidebarContactLinkExtension
)
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.models.extensions import VisibleOnHomepageExtension
from onegov.org.models.extensions import SidebarLinksExtension
from onegov.org.models.traitinfo import TraitInfo
from onegov.org.observer import observes
from onegov.page import Page
from onegov.page.collection import AdjacencyListCollection, PageCollection
from onegov.search import SearchableContent
from sedate import replace_timezone
from sqlalchemy import desc, func, or_, and_
from sqlalchemy.dialects.postgresql import array, JSON
from sqlalchemy.orm import undefer, object_session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest, PageMeta
    from sqlalchemy.orm import Query, Session
    from typing import Self


class Topic(Page, TraitInfo, SearchableContent, AccessExtension,
            PublicationExtension, VisibleOnHomepageExtension,
            ContactExtension, ContactHiddenOnPageExtension,
            PeopleShownOnMainPageExtension, PersonLinkExtension,
            CoordinatesExtension, ImageExtension,
            GeneralFileLinkExtension, SidebarLinksExtension,
            SidebarContactLinkExtension, InlinePhotoAlbumExtension):

    __mapper_args__ = {'polymorphic_identity': 'topic'}

    es_type_name = 'topics'

    lead: dict_property[str | None] = content_property()
    text = dict_markup_property('content')
    url: dict_property[str | None] = content_property()
    as_card: dict_property[str | None] = content_property()
    height: dict_property[str | None] = content_property()

    # Show the lead on topics page
    lead_when_child: dict_property[bool] = content_property(default=True)

    @property
    def es_skip(self) -> bool:
        return self.meta.get('trait') == 'link'  # do not index links

    @property
    def es_public(self) -> bool:
        return self.access == 'public' and self.published

    @property
    def deletable(self) -> bool:
        """ Returns true if this page may be deleted. """
        return True

    @property
    def editable(self) -> bool:
        return True

    @property
    def url_changeable(self) -> bool:
        """Open for all topics, even root ones."""
        return True

    @property
    def paste_target(self) -> Topic | News:
        if self.trait == 'link':
            return self.parent or self  # type:ignore[return-value]

        if self.trait == 'page':
            return self

        raise NotImplementedError

    @property
    def allowed_subtraits(self) -> tuple[str, ...]:
        if self.trait == 'link':
            return ()

        if self.trait == 'page':
            return ('page', 'link', 'iframe')

        if self.trait == 'iframe':
            return ()

        raise NotImplementedError

    def is_supported_trait(self, trait: str) -> bool:
        return trait in {'link', 'page', 'iframe'}

    def get_form_class(
        self,
        trait: str,
        action: str,
        request: OrgRequest
    ) -> type[LinkForm | PageForm | IframeForm]:

        if trait == 'link':
            return self.with_content_extensions(LinkForm, request, extensions=[
                AccessExtension,
                VisibleOnHomepageExtension
            ])

        if trait == 'page':
            return move_fields(
                form_class=self.with_content_extensions(PageForm, request),
                fields=(
                    'page_image',
                    'show_preview_image',
                    'show_page_image'
                ),
                after='title'
            )

        if trait == 'iframe':
            return self.with_content_extensions(
                IframeForm, request, extensions=[
                    AccessExtension,
                    VisibleOnHomepageExtension
                ])

        raise NotImplementedError


class News(Page, TraitInfo, SearchableContent, NewsletterExtension,
           AccessExtension, PublicationExtension, VisibleOnHomepageExtension,
           ContactExtension, ContactHiddenOnPageExtension,
           PeopleShownOnMainPageExtension, PersonLinkExtension,
           CoordinatesExtension, ImageExtension, GeneralFileLinkExtension,
           DeletableContentExtension, InlinePhotoAlbumExtension):

    __mapper_args__ = {'polymorphic_identity': 'news'}

    es_type_name = 'news'

    lead: dict_property[str | None] = content_property()
    text = dict_markup_property('content')
    url: dict_property[str | None] = content_property()

    filter_years: list[int] = []
    filter_tags: list[str] = []

    hashtags: dict_property[list[str]] = meta_property(default=list)

    @property
    def es_public(self) -> bool:
        return self.access == 'public' and self.published

    @observes('content')
    def content_observer(self, content: dict[str, Any]) -> None:
        self.hashtags = self.es_tags or []

    @property
    def absorb(self) -> str:  # type:ignore[override]
        return ''.join(self.path.split('/', 1)[1:])

    @property
    def deletable(self) -> bool:
        return self.parent_id is not None

    @property
    def editable(self) -> bool:
        return True

    @property
    def url_changeable(self) -> bool:
        """Open for all topics, even root ones."""
        return self.parent_id is not None

    @property
    def paste_target(self) -> Topic | News:
        if self.parent:
            return self.parent  # type:ignore[return-value]
        else:
            return self

    @property
    def allowed_subtraits(self) -> tuple[str, ...]:
        # only allow one level of news
        if self.parent is None:
            return ('news', )
        else:
            return ()

    def is_supported_trait(self, trait: str) -> bool:
        return trait in {'news'}

    def get_root_page_form_class(self, request: OrgRequest) -> type[Form]:
        return self.with_content_extensions(
            Form, request, extensions=(
                ContactExtension, ContactHiddenOnPageExtension,
                PersonLinkExtension, AccessExtension
            )
        )

    def get_form_class(
        self,
        trait: str,
        action: str,
        request: OrgRequest
    ) -> type[Form | PageForm]:

        if trait == 'news':
            if not self.parent and action == 'edit':
                return self.get_root_page_form_class(request)
            form_class = self.with_content_extensions(PageForm, request)

            if hasattr(form_class, 'is_visible_on_homepage'):
                # clarify the intent of this particular flag on the news, as
                # the effect is not entirely the same (news may be shown on the
                # homepage anyway)
                form_class.is_visible_on_homepage.kwargs['label'] = _(
                    'Always visible on homepage')

            form_class = move_fields(
                form_class=form_class,
                fields=(
                    'page_image',
                    'show_preview_image',
                    'show_page_image'
                ),
                after='title'
            )

            return form_class

        raise NotImplementedError

    def for_year(self, year: int) -> News:
        years_ = set(self.filter_years)
        years = list(years_ - {year} if year in years_ else years_ | {year})
        return News(  # type:ignore[misc]
            id=self.id,
            title=self.title,
            name=self.name,
            filter_years=sorted(years),
            filter_tags=sorted(self.filter_tags)
        )

    def for_tag(self, tag: str) -> News:
        tags_ = set(self.filter_tags)
        tags = list(tags_ - {tag} if tag in tags_ else tags_ | {tag})
        return News(  # type:ignore[misc]
            id=self.id,
            title=self.title,
            name=self.name,
            filter_years=sorted(self.filter_years),
            filter_tags=sorted(tags)
        )

    @classmethod
    def news_query_for(
        cls,
        self: News | PageMeta,
        limit: int | None = 2,
        published_only: bool = True,
        session: Session | None = None,
    ) -> Query[News]:

        if session is None:
            session = object_session(self)

        news = session.query(News)
        if isinstance(self, News):
            # avoid a redundant relationship load when we can
            news = news.filter(Page.parent == self)
        else:
            news = news.filter(Page.parent_id == self.id)

        if published_only:
            news = news.filter(
                News.publication_started == True,
                News.publication_ended == False
            )

        year_filters = []
        for year in getattr(self, 'filter_years', ()):
            start = replace_timezone(datetime(year, 1, 1), 'UTC')
            year_filters.append(
                and_(
                    News.published_or_created >= start,
                    News.published_or_created < start.replace(year=year + 1)
                )
            )
        if year_filters:
            news = news.filter(or_(*year_filters))

        if filter_tags := getattr(self, 'filter_tags', None):
            news = news.filter(
                News.meta['hashtags'].has_any(array(filter_tags))
            )

        news = news.order_by(desc(News.published_or_created))
        news = news.options(undefer('created'))
        news = news.options(undefer('content'))
        news = news.limit(limit)

        sticky = func.json_extract_path_text(
            func.cast(News.meta, JSON), 'is_visible_on_homepage') == 'true'

        sticky_news = news.limit(None)
        sticky_news = sticky_news.filter(sticky)

        return news.union(sticky_news).order_by(
            desc(News.published_or_created))

    def news_query(
        self,
        limit: int | None = 2,
        published_only: bool = True
    ) -> Query[News]:

        return self.news_query_for(self, limit, published_only)

    @property
    def all_years(self) -> list[int]:
        query = object_session(self).query(News)
        query = query.with_entities(
            func.date_part('year', Page.published_or_created))
        query = query.group_by(
            func.date_part('year', Page.published_or_created))
        query = query.filter(Page.parent == self)
        return sorted((int(year) for year, in query), reverse=True)

    @property
    def all_tags(self) -> list[str]:
        query = object_session(self).query(News.meta['hashtags'])
        query = query.filter(Page.parent == self)
        all_hashtags = set()
        for hashtags, in query:
            all_hashtags.update(hashtags)
        return sorted(all_hashtags)


class TopicCollection(Pagination[Topic], AdjacencyListCollection[Topic]):
    """
    Use it like this:

        from onegov.page import TopicCollection
        topics = TopicCollection(session)
    """

    __listclass__ = Topic

    def __init__(
        self,
        session: Session,
        page: int = 0,
    ):
        self.session = session
        self.page = page

    def subset(self) -> Query[Topic]:
        topics = self.session.query(Topic)
        topics = topics.filter(
            News.publication_started == True,
            News.publication_ended == False
        )
        topics = topics.order_by(desc(Topic.published_or_created))
        topics = topics.options(undefer('created'))
        topics = topics.options(undefer('content'))
        return topics

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index
        )


class NewsCollection(Pagination[News], AdjacencyListCollection[News]):
    """
    Use it like this:

        from onegov.page import NewsCollection
        news = NewsCollection(session)
    """

    __listclass__ = News

    def __init__(
        self,
        session: Session,
        page: int = 0,
    ):
        self.session = session
        self.page = page

    def subset(self) -> Query[News]:
        parent = PageCollection(self.session).by_path(
            '/news/', ensure_type='news')
        news = self.session.query(News)
        if parent:
            news = news.filter(Page.parent_id == parent.id)
        news = news.filter(
            News.publication_started == True,
            News.publication_ended == False
        )
        news = news.order_by(desc(News.published_or_created))
        news = news.options(undefer('created'))
        news = news.options(undefer('content'))
        return news

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.session,
            page=index
        )


class AtoZPages(AtoZ[Topic]):

    def get_title(self, item: Topic) -> str:
        return item.title

    def get_items(self) -> list[Topic]:

        # XXX implement correct collation support on the database level
        topics = self.request.session.query(Topic).all()
        topics = sorted(topics, key=self.sortkey)

        if self.request.is_manager:
            return [topic for topic in topics if topic.trait == 'page']
        else:
            return [
                topic for topic in topics if topic.trait == 'page'
                and topic.access == 'public'
            ]
