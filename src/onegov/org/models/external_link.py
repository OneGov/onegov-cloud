from uuid import uuid4

from onegov.core.collection import GenericCollection
from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property, ContentMixin, \
    TimestampMixin
from onegov.core.orm.types import UUID
from onegov.core.utils import normalize_for_url
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

    # For example the collection name this model should appear in
    member_of = Column(Text, nullable=True)
    group = Column(Text, nullable=True)

    #: The normalized title for sorting
    order = Column(Text, nullable=False, index=True)

    es_type_name = 'external_links'
    es_id = 'title'

    lead = content_property()

    @observes('title')
    def title_observer(self, title):
        self.order = normalize_for_url(title)


class ExternalLinkCollection(GenericCollection):

    def __init__(
            self, session, member_of=None, group=None, to=None, title=None):
        super().__init__(session)
        self.member_of = member_of
        self.group = group

        # used to redirect and the views
        self.to = to
        self.title = title

    @property
    def model_class(self):
        return ExternalLink

    def query(self):
        query = super().query()
        if self.member_of:
            query = query.filter_by(member_of=self.member_of)
        if self.group:
            query = query.filter_by(group=self.group)
        return query

    @classmethod
    def for_model(cls, session, model, **kwargs):
        return cls(session, member_of=model.__class__.__name__, **kwargs)
