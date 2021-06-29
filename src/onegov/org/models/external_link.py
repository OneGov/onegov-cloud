from uuid import uuid4

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin, \
    TimestampMixin, meta_property
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
from onegov.form import FormCollection
from onegov.org.models import AccessExtension
from onegov.search import SearchableContent
from sqlalchemy import Column, Text
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

    # The collection name this model should appear in
    member_of = Column(Text, nullable=True)
    group = Column(Text, nullable=True)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    es_type_name = 'external_links'
    es_id = 'title'

    lead = meta_property()

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)


class ExternalLinkCollection(GenericCollection):

    supported_collections = (
        FormCollection,
    )

    def __init__(
            self, session, member_of=None, group=None):
        super().__init__(session)
        self.member_of = member_of
        self.group = group

    @staticmethod
    def translatable_name(model_class):
        """ Most collections have a base model whose name can be guessed
         from the collection name. """
        name = model_class.__name__.lower()
        name = name.replace('collection', '').rstrip('s')
        return f'{name.capitalize()}s'

    @classmethod
    def form_choices(cls):
        return tuple(
            (m.__name__, cls.translatable_name(m))
            for m in cls.supported_collections
        )

    @classmethod
    def collection_by_name(cls):
        return {m.__name__: m for m in cls.supported_collections}

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

        assert model_class in cls.supported_collections, model_class.__name__
        return cls(session, member_of=model_class.__name__, **kwargs)
