from __future__ import annotations

from datetime import datetime
from functools import cached_property
from onegov.core.collection import Pagination
from onegov.core.orm.abstract import AdjacencyListCollection
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
    InlinePhotoAlbumExtension, SidebarContactLinkExtension,
    PushNotificationExtension
)
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.models.extensions import VisibleOnHomepageExtension
from onegov.org.models.extensions import SidebarLinksExtension
from onegov.org.models.traitinfo import TraitInfo
from onegov.org.observer import observes
from onegov.page import Page, PageCollection
from onegov.search import SearchableContent
from sedate import replace_timezone
from sqlalchemy import desc, func, or_, and_
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import undefer, object_session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.org.request import OrgRequest
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
           DeletableContentExtension, InlinePhotoAlbumExtension,
           PushNotificationExtension):

    __mapper_args__ = {'polymorphic_identity': 'news'}

    es_type_name = 'news'

    filter_years = None
    filter_tags = None
    page = None

    lead: dict_property[str | None] = content_property()
    text = dict_markup_property('content')
    url: dict_property[str | None] = content_property()

    hashtags: dict_property[list[str]] = meta_property(default=list)

    push_notifications: dict_property[list[list[str]]] = (
        meta_property(default=list)
    )
    send_push_notifications_to_app: dict_property[bool] = meta_property(
        default=False
    )

    @property
    def es_public(self) -> bool:
        return self.access == 'public' and self.published

    @observes('content')
    def content_observer(self, content: dict[str, Any]) -> None:
        self.hashtags = self.es_tags or []

    @property
    def absorb(self) -> str:
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

    @property
    def es_last_change(self) -> datetime:
        return self.published_or_created

    def is_supported_trait(self, trait: str) -> bool:
        return trait == 'news'

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

            if hasattr(form_class, 'send_push_notifications_to_app'):
                form_class = move_fields(
                    form_class=form_class,
                    fields=(
                        'send_push_notifications_to_app',
                        'push_notifications',
                    ),
                    after='publication_start'
                )

            return form_class

        raise NotImplementedError

    def push_notifications_were_sent_before(self) -> bool:
        from onegov.org.models import PushNotification
        session = object_session(self)
        query = session.query(PushNotification).filter(
            PushNotification.news_id == self.id)
        return session.query(query.exists()).scalar()


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
        only_public: bool = False,
    ):
        self.session = session
        self.page = page
        self.only_public = only_public

    def subset(self) -> Query[Topic]:
        topics = self.session.query(Topic)
        if self.only_public:
            topics = topics.filter(or_(
                Topic.meta['access'].astext == 'public',
                Topic.meta['access'].is_(None)
            ))

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
        news = NewsCollection(request)
    """

    __listclass__ = News
    batch_size = 40
    absorb = ''

    def __init__(
        self,
        request: CoreRequest,
        page: int = 0,
        filter_years: list[int] | None = None,
        filter_tags: list[str] | None = None,
        root: News | None = None,
    ) -> None:

        self.request = request
        self.session = request.session
        self.page = page
        self.filter_years = filter_years or []
        self.filter_tags = filter_tags or []
        if root is not None:
            self.root = root

    @cached_property
    def root(self) -> News | None:
        pages = PageCollection(self.session)
        return pages.by_path(  # type: ignore[return-value]
            '/news/', ensure_type='news'
        ) or pages.by_path(
            '/aktuelles/', ensure_type='news'
        )

    @property
    def access(self) -> str:
        return self.root.access if self.root else 'public'

    def subset(self) -> Query[News]:
        news = self.session.query(News)

        if self.root is not None:
            news = news.filter(News.parent == self.root)

        role = getattr(self.request.identity, 'role', 'anonymous')
        available_accesses = {
            'admin': (),  # can see everything
            'editor': (),  # can see everything
            'member': ('member', 'mtan', 'public')
        }.get(role, ('mtan', 'public'))
        if available_accesses:
            news = news.filter(or_(
                *(
                    News.meta['access'].astext == access
                    for access in available_accesses
                ),
                News.meta['access'].is_(None)
            ))

        if role not in ('admin', 'editor'):
            news = news.filter(
                News.publication_started == True,
                News.publication_ended == False
            )

        if self.filter_years:
            news = news.filter(or_(*(
                and_(
                    News.published_or_created >= (
                        start := replace_timezone(datetime(year, 1, 1), 'UTC')
                    ),
                    News.published_or_created < start.replace(year=year + 1)
                )
                for year in self.filter_years
            )))

        if self.filter_tags:
            news = news.filter(
                News.meta['hashtags'].has_any(array(self.filter_tags))  # type: ignore[call-overload]
            )

        news = news.order_by(desc(News.published_or_created))
        news = news.options(undefer('created'))
        news = news.options(undefer('content'))
        return news

    def sticky(self) -> Query[News]:
        """Get a query with only the sticky news."""
        return self.subset().filter(
            News.meta['is_visible_on_homepage'].astext == 'true'
        )

    @property
    def page_index(self) -> int:
        return self.page

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.filter_years == other.filter_years
            and self.filter_tags == other.filter_tags
        )

    def page_by_index(self, index: int) -> Self:
        return self.__class__(
            self.request,
            page=index,
            filter_years=sorted(self.filter_years),
            filter_tags=sorted(self.filter_tags),
        )

    def for_year(self, year: int) -> Self:
        years_ = set(self.filter_years)
        years = sorted(years_ - {year} if year in years_ else years_ | {year})
        return self.__class__(
            self.request,
            filter_years=years,
            filter_tags=sorted(self.filter_tags),
        )

    def for_tag(self, tag: str) -> Self:
        tags_ = set(self.filter_tags)
        tags = sorted(tags_ - {tag} if tag in tags_ else tags_ | {tag})
        return self.__class__(
            self.request,
            filter_years=sorted(self.filter_years),
            filter_tags=tags,
        )

    @property
    def all_years(self) -> list[int]:
        query = self.session.query(
            func.date_part('year', News.published_or_created))
        query = query.filter(News.parent == self.root)
        query = query.distinct()
        return sorted((int(year) for year, in query), reverse=True)

    @property
    def all_tags(self) -> list[str]:
        query = self.session.query(
            func.jsonb_array_elements_text(News.meta['hashtags']))
        query = query.filter(Page.parent == self.root)
        query = query.distinct()
        return sorted(hashtag for hashtag, in query)

    def __link_alias__(self) -> str:
        return self.request.class_link(
            News,
            {
                'absorb': None,
                'filter_years': self.filter_years,
                'filter_tags': self.filter_tags,
                'page': self.page
            }
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
