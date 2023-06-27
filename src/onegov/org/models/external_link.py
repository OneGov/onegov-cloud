from uuid import uuid4

from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, \
    TimestampMixin, meta_property
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection
from onegov.reservation import ResourceCollection
from onegov.org.models import AccessExtension
from onegov.search import SearchableContent, Searchable
from sqlalchemy import Column, Text, Index
from sqlalchemy import Computed  # type:ignore[attr-defined]
from sqlalchemy_utils import observes


class ExternalLink(Base, ContentMixin, TimestampMixin, AccessExtension,
                   SearchableContent):
    """
    An Object appearing in some other collection
    that features a lead and text but points to some external url.
    """

    __tablename__ = 'external_links'

    es_properties = {
        'title': {'type': 'localized'},
        'lead': {'type': 'localized'},
    }

    id = Column(UUID, primary_key=True, default=uuid4)

    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    page_image = meta_property()

    # The collection name this model should appear in
    member_of = Column(Text, nullable=True)
    # TODO: Stop passing title (and maybe even to) as url parameters.
    # Figure out a way to use the member_of attribute instead.
    group = Column(Text, nullable=True)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    es_type_name = 'external_links'
    es_id = 'title'

    lead = meta_property()

    fts_idx = Column(TSVECTOR, Computed('', persisted=True))

    __table_args__ = (
        Index('fts_idx', fts_idx, postgresql_using='gin'),
    )

    @property
    def search_score(self):
        return 8

    @staticmethod
    def psql_tsvector_string():
        """
        builds the index on column title and lead within meta column
        email.
        """
        s = Searchable.create_tsvector_string('title')
        s += " || ' ' || coalesce(((meta ->> 'lead')), '')"
        return s

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)


class ExternalLinkCollection(GenericCollection):

    supported_collections = {
        'form': FormCollection,
        'resource': ResourceCollection
    }

    def __init__(
            self, session, member_of=None, group=None, type=None):
        super().__init__(session)
        self.member_of = member_of
        self.group = group
        self.type = type

    @staticmethod
    def translatable_name(model_class):
        """ Most collections have a base model whose name can be guessed
         from the collection name. """
        name = model_class.__name__.lower()
        name = name.replace('collection', '').rstrip('s')
        return f'{name.capitalize()}s'

    def form_choices(self):
        if self.type in self.supported_collections:
            collection = self.supported_collections[self.type]
            return (
                (collection.__name__, self.translatable_name(collection)),
            )
        else:
            return tuple(
                (m.__name__, self.translatable_name(m))
                for m in self.supported_collections.values()
            )

    @classmethod
    def collection_by_name(cls):
        return {m.__name__: m for m in cls.supported_collections.values()}

    @property
    def model_class(self):
        return ExternalLink

    @classmethod
    def target(cls, external_link):
        return cls.collection_by_name()[external_link.member_of]

    def query(self):
        query = super().query()
        if self.member_of:
            query = query.filter_by(member_of=self.member_of)
        if self.group:
            query = query.filter_by(group=self.group)
        return query

    @classmethod
    def for_model(cls, session, model_class, **kwargs):
        """ It would be better to use the tablename, but the collections do
        not always implement the property model_class. """

        assert model_class in cls.supported_collections.values()
        return cls(session, member_of=model_class.__name__, **kwargs)
