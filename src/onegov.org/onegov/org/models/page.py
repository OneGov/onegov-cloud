from onegov.core import utils
from onegov.core.orm.mixins import content_property
from onegov.page import Page
from onegov.search import ORMSearchable
from onegov.org.forms import LinkForm, PageForm
from onegov.org.models.atoz import AtoZ
from onegov.org.models.extensions import (
    ContactExtension,
    CoordinatesExtension,
    HiddenFromPublicExtension,
    PersonLinkExtension,
    VisibleOnHomepageExtension,
)
from onegov.org.models.traitinfo import TraitInfo
from sqlalchemy import desc, func
from sqlalchemy.orm import undefer, object_session


class SearchablePage(ORMSearchable):

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
        'text': {'type': 'localized_html'}
    }

    lead = content_property('lead')
    text = content_property('text')
    url = content_property('url')

    @property
    def es_public(self):
        return not self.is_hidden_from_public

    @property
    def es_language(self):
        return 'de'  # xxx for now there's no other language

    @property
    def es_skip(self):
        return self.meta.get('trait') == 'link'  # do not index links

    @property
    def es_suggestions(self):
        return {
            "input": [self.title.lower()]
        }


class Topic(Page, TraitInfo, SearchablePage, HiddenFromPublicExtension,
            VisibleOnHomepageExtension, ContactExtension, PersonLinkExtension,
            CoordinatesExtension):
    __mapper_args__ = {'polymorphic_identity': 'topic'}

    es_type_name = 'topics'

    @property
    def deletable(self):
        """ Returns true if this page may be deleted. """
        return self.parent is not None

    @property
    def editable(self):
        return True

    @property
    def paste_target(self):
        if self.trait == 'link':
            return self.parent

        if self.trait == 'page':
            return self

        raise NotImplementedError

    @property
    def allowed_subtraits(self):
        if self.trait == 'link':
            return tuple()

        if self.trait == 'page':
            return ('page', 'link')

        raise NotImplementedError

    def is_supported_trait(self, trait):
        return trait in {'link', 'page'}

    def get_form_class(self, trait, request):
        if trait == 'link':
            return self.with_content_extensions(LinkForm, request, extensions=[
                HiddenFromPublicExtension,
                VisibleOnHomepageExtension
            ])

        if trait == 'page':
            return self.with_content_extensions(PageForm, request)

        raise NotImplementedError


class News(Page, TraitInfo, SearchablePage,
           HiddenFromPublicExtension, ContactExtension, PersonLinkExtension,
           CoordinatesExtension):
    __mapper_args__ = {'polymorphic_identity': 'news'}

    es_type_name = 'news'

    @property
    def absorb(self):
        return utils.lchop(self.path, 'aktuelles').lstrip('/')

    @property
    def deletable(self):
        return self.parent is not None

    @property
    def editable(self):
        return self.parent is not None

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
            return tuple()

    def is_supported_trait(self, trait):
        return trait in {'news'}

    def get_form_class(self, trait, request):
        if trait == 'news':
            return self.with_content_extensions(PageForm, request)

        raise NotImplementedError

    @property
    def news_query(self):
        query = object_session(self).query(News)
        query = query.filter(Page.parent == self)
        query = query.order_by(desc(Page.created))
        query = query.options(undefer('created'))
        query = query.options(undefer('content'))

        return query

    @property
    def years(self):
        query = object_session(self).query(News)
        query = query.with_entities(func.date_part('year', Page.created))
        query = query.group_by(func.date_part('year', Page.created))
        query = query.filter(Page.parent == self)

        return sorted([int(r[0]) for r in query.all()], reverse=True)


class AtoZPages(AtoZ):

    def get_title(self, item):
        return item.title

    def get_items(self):

        # XXX implement correct collation support on the database level
        topics = self.request.app.session().query(Topic).all()
        topics = sorted(topics, key=self.sortkey)

        if self.request.is_manager:
            return [topic for topic in topics if topic.trait == 'page']
        else:
            return [
                topic for topic in topics if topic.trait == 'page' and
                not topic.is_hidden_from_public
            ]
