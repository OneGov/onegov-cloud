from datetime import datetime
from onegov.core.orm.mixins import (
    content_property, dict_property, meta_property)
from onegov.file import MultiAssociatedFiles
from onegov.form import Form, move_fields
from onegov.org import _
from onegov.org.forms import LinkForm, PageForm
from onegov.org.models.atoz import AtoZ
from onegov.org.models.extensions import (
    ContactExtension, ContactHiddenOnPageExtension, ImageExtension,
    NewsletterExtension, PublicationExtension
)
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.extensions import CoordinatesExtension
from onegov.org.models.extensions import GeneralFileLinkExtension
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.models.extensions import VisibleOnHomepageExtension
from onegov.org.models.traitinfo import TraitInfo
from onegov.page import Page
from onegov.search import SearchableContent
from sedate import replace_timezone
from sqlalchemy import desc, func, or_, and_
from sqlalchemy.dialects.postgresql import array, JSON
from sqlalchemy.orm import undefer, object_session
from sqlalchemy_utils import observes


class Topic(Page, TraitInfo, SearchableContent, AccessExtension,
            PublicationExtension, VisibleOnHomepageExtension,
            ContactExtension, ContactHiddenOnPageExtension,
            PersonLinkExtension, CoordinatesExtension, ImageExtension,
            MultiAssociatedFiles, GeneralFileLinkExtension):

    __mapper_args__ = {'polymorphic_identity': 'topic'}

    es_type_name = 'topics'

    lead = content_property()
    text = content_property()
    url = content_property()

    # Show the lead on topics page
    lead_when_child = content_property(default=True)

    @property
    def es_skip(self):
        return self.meta.get('trait') == 'link'  # do not index links

    @property
    def es_public(self):
        return self.access == 'public' and self.published

    @property
    def deletable(self):
        """ Returns true if this page may be deleted. """
        return self.parent is not None

    @property
    def editable(self):
        return True

    @property
    def url_changeable(self):
        """Open for all topics, even root ones."""
        return True

    @property
    def paste_target(self):
        if self.trait == 'link':
            return self.parent or self

        if self.trait == 'page':
            return self

        raise NotImplementedError

    @property
    def allowed_subtraits(self):
        if self.trait == 'link':
            return ()

        if self.trait == 'page':
            return ('page', 'link')

        raise NotImplementedError

    def is_supported_trait(self, trait):
        return trait in {'link', 'page'}

    def get_form_class(self, trait, action, request):
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

        raise NotImplementedError


class News(Page, TraitInfo, SearchableContent, NewsletterExtension,
           AccessExtension, PublicationExtension, VisibleOnHomepageExtension,
           ContactExtension, ContactHiddenOnPageExtension, PersonLinkExtension,
           CoordinatesExtension, ImageExtension, MultiAssociatedFiles,
           GeneralFileLinkExtension):

    __mapper_args__ = {'polymorphic_identity': 'news'}

    es_type_name = 'news'

    lead = content_property()
    text = content_property()
    url = content_property()

    filter_years: list[int] = []
    filter_tags: list[str] = []

    hashtags: dict_property[list[str]] = meta_property(default=list)

    @property
    def es_public(self):
        return self.access == 'public' and self.published

    @observes('content')
    def content_observer(self, files):
        self.hashtags = self.es_tags or []

    @property
    def absorb(self):
        return ''.join(self.path.split('/', 1)[1:])

    @property
    def deletable(self):
        return self.parent_id is not None

    @property
    def editable(self):
        return True

    @property
    def url_changeable(self):
        """Open for all topics, even root ones."""
        return self.parent_id is not None

    @property
    def paste_target(self):
        if self.parent:
            return self.parent
        else:
            return self

    @property
    def allowed_subtraits(self):
        # only allow one level of news
        if self.parent is None:
            return ('news', )
        else:
            return ()

    def is_supported_trait(self, trait):
        return trait in {'news'}

    def get_root_page_form_class(self, request):
        return self.with_content_extensions(
            Form, request, extensions=(
                ContactExtension, ContactHiddenOnPageExtension,
                PersonLinkExtension, AccessExtension
            )
        )

    def get_form_class(self, trait, action, request):
        if trait == 'news':
            if not self.parent and action == 'edit':
                return self.get_root_page_form_class(request)
            form_class = self.with_content_extensions(PageForm, request)

            if hasattr(form_class, 'is_visible_on_homepage'):
                # clarify the intent of this particular flag on the news, as
                # the effect is not entirely the same (news may be shown on the
                # homepage anyway)
                form_class.is_visible_on_homepage.kwargs['label'] = _(
                    "Always visible on homepage")

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

    def for_year(self, year):
        years = set(self.filter_years)
        years = list(years - {year} if year in years else years | {year})
        return News(
            id=self.id,
            title=self.title,
            name=self.name,
            filter_years=sorted(years),
            filter_tags=sorted(self.filter_tags)
        )

    def for_tag(self, tag):
        tags = set(self.filter_tags)
        tags = list(tags - {tag} if tag in tags else tags | {tag})
        return News(
            id=self.id,
            title=self.title,
            name=self.name,
            filter_years=sorted(self.filter_years),
            filter_tags=sorted(tags)
        )

    def news_query(self, limit=2, published_only=True):
        news = object_session(self).query(News)
        news = news.filter(Page.parent == self)
        if published_only:
            news = news.filter(
                News.publication_started == True,
                News.publication_ended == False
            )

        filter = []
        for year in self.filter_years:
            start = replace_timezone(datetime(year, 1, 1), 'UTC')
            filter.append(
                and_(
                    News.published_or_created >= start,
                    News.published_or_created < start.replace(year=year + 1)
                )
            )
        if filter:
            news = news.filter(or_(*filter))

        if self.filter_tags:
            news = news.filter(
                News.meta['hashtags'].has_any(array(self.filter_tags))
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

    @property
    def all_years(self):
        query = object_session(self).query(News)
        query = query.with_entities(
            func.date_part('year', Page.published_or_created))
        query = query.group_by(
            func.date_part('year', Page.published_or_created))
        query = query.filter(Page.parent == self)
        return sorted([int(r[0]) for r in query.all()], reverse=True)

    @property
    def all_tags(self):
        query = object_session(self).query(News.meta['hashtags'])
        query = query.filter(Page.parent == self)
        hashtags = set()
        for result in query.all():
            hashtags.update(set(result[0]))
        return sorted(hashtags)


class AtoZPages(AtoZ):

    def get_title(self, item):
        return item.title

    def get_items(self):

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
